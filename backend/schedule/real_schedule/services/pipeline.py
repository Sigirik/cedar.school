# backend/schedule/real_schedule/services/pipeline.py
# Генерация RealLesson из активной/заданной шаблонной недели + привязка к KTP по дате плана.
# Валидации базовые (длительность>0).
# Пересечения по дате/времени (teacher/grade) проверяем внутри создаваемого набора.

import uuid
import datetime as dt
from datetime import timezone as dt_timezone
from dataclasses import dataclass
from typing import Iterable

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from schedule.real_schedule.models import RealLesson
from schedule.template.models import ActiveTemplateWeek, TemplateLesson
from schedule.ktp.models import KTPEntry


@dataclass
class GenerateResult:
    version: int
    generation_batch_id: str
    deleted: int
    created: int
    warnings: list


def _active_template_week_id() -> int | None:
    atw = ActiveTemplateWeek.objects.select_related("template").first()
    return atw.template_id if atw else None


def _iter_dates(d_from: dt.date, d_to: dt.date) -> Iterable[dt.date]:
    cur = d_from
    while cur <= d_to:
        yield cur
        cur += dt.timedelta(days=1)


def _collect_template_lessons_for_range(template_week_id: int, d_from: dt.date, d_to: dt.date):
    """
    Для каждого дня в интервале [from..to] подбираем уроки шаблона по day_of_week.
    Возвращает итератор с dict-ами для сборки RealLesson.
    """
    lessons = list(
        TemplateLesson.objects.filter(template_week_id=template_week_id)
        .select_related("subject", "grade", "teacher", "type")
        .order_by("day_of_week", "start_time")
    )

    by_weekday: dict[int, list[TemplateLesson]] = {}
    for tl in lessons:
        by_weekday.setdefault(tl.day_of_week, []).append(tl)

    for date in _iter_dates(d_from, d_to):
        weekday = date.weekday()  # 0=Mon
        for tl in by_weekday.get(weekday, []):
            yield {"real_date": date, "template_lesson": tl}


def _find_ktp_entry(subject_id: int, grade_id: int, date_: dt.date, template_lesson_id: int | None):
    """
    Ищем KTPEntry по planned_date + пара (subject, grade).
    Если есть несколько — приоритет тем, где template_lesson совпадает.
    """
    qs = (
        KTPEntry.objects.select_related("section__ktp_template")
        .filter(
            section__ktp_template__subject_id=subject_id,
            section__ktp_template__grade_id=grade_id,
            planned_date=date_,
        )
        .order_by("order")
    )
    if template_lesson_id:
        with_tl = qs.filter(template_lesson_id=template_lesson_id).first()
        if with_tl:
            return with_tl
    return qs.first()


def _validate_collisions(new_lessons: list[RealLesson]):
    """
    Простая проверка пересечений по учителю/классу в рамках создаваемого набора — по точным датам.
    """
    from collections import defaultdict

    by_date_teacher = defaultdict(list)  # (date, teacher_id) -> [(start, end, idx)]
    by_date_grade = defaultdict(list)    # (date, grade_id)   -> [(start, end, idx)]

    for idx, rl in enumerate(new_lessons):
        end = rl.start + dt.timedelta(minutes=rl.duration_minutes)
        d = rl.start.date()
        by_date_teacher[(d, rl.teacher_id)].append((rl.start, end, idx))
        by_date_grade[(d, rl.grade_id)].append((rl.start, end, idx))

    def overlaps(items):
        items.sort(key=lambda x: (x[0], x[1]))
        for i in range(len(items) - 1):
            s1, e1, _ = items[i]
            s2, e2, _ = items[i + 1]
            if s2 < e1:
                return True
        return False

    for key, items in by_date_teacher.items():
        if overlaps(items):
            raise ValueError(f"OVERLAP_TEACHER on {key}")
    for key, items in by_date_grade.items():
        if overlaps(items):
            raise ValueError(f"OVERLAP_GRADE on {key}")


@transaction.atomic
def generate(
    from_date: dt.date,
    to_date: dt.date,
    template_week_id: int | None = None,
    rewrite_from: dt.date | None = None,
) -> GenerateResult:
    """
    1) Жёстко удаляем все RealLesson с source=TEMPLATE и start >= rewrite_from
    2) Генерируем новые занятия на [from..to] по TemplateLesson, связываем с KTPEntry через planned_date
    """
    assert from_date <= to_date
    if template_week_id is None:
        template_week_id = _active_template_week_id()
    if template_week_id is None:
        raise ValueError("NO_ACTIVE_TEMPLATE")

    if rewrite_from is None:
        rewrite_from = from_date

    # Удаление TEMPLATE с нужной даты
    tz = dt_timezone.utc  # TIME_ZONE не указан — работаем в UTC
    rewrite_from_utc = timezone.make_aware(
        dt.datetime.combine(rewrite_from, dt.time.min),
        tz,
    )
    deleted, _ = RealLesson.objects.filter(
        source=RealLesson.Source.TEMPLATE, start__gte=rewrite_from_utc
    ).delete()

    prev_version = RealLesson.objects.aggregate(m=Max("version"))["m"] or 0
    new_version = prev_version + 1
    batch_id = uuid.uuid4()

    # Загружаем уроки шаблона и собираем набор RealLesson
    to_insert: list[RealLesson] = []
    warnings: list[dict] = []

    for item in _collect_template_lessons_for_range(template_week_id, from_date, to_date):
        tl: TemplateLesson = item["template_lesson"]
        date_ = item["real_date"]

        start_dt = timezone.make_aware(
            dt.datetime.combine(date_, tl.start_time),
            tz,
        )
        rl = RealLesson(
            subject_id=tl.subject_id,
            grade_id=tl.grade_id,
            teacher_id=tl.teacher_id,
            start=start_dt,
            duration_minutes=tl.duration_minutes,
            lesson_type_id=tl.type_id,
            source=RealLesson.Source.TEMPLATE,
            template_week_id=template_week_id,
            template_lesson_id=tl.id,
            generation_batch_id=batch_id,
            version=new_version,
        )

        # Привязка к KTPEntry по planned_date
        entry = _find_ktp_entry(tl.subject_id, tl.grade_id, date_, tl.id)
        if entry:
            rl.ktp_entry_id = entry.id
            rl.topic_order = entry.order
            rl.topic_title = entry.title
        else:
            warnings.append(
                {
                    "code": "KTP_MISS",
                    "message": f"Нет KTPEntry для {date_} {tl.grade_id}/{tl.subject_id}",
                }
            )

        if rl.duration_minutes <= 0:
            raise ValueError("MISSING_OR_INVALID_DURATION")

        to_insert.append(rl)

    # Валидации пересечений внутри создаваемого набора
    _validate_collisions(to_insert)

    # Вставка
    RealLesson.objects.bulk_create(to_insert, batch_size=500)

    return GenerateResult(
        version=new_version,
        generation_batch_id=str(batch_id),
        deleted=deleted,
        created=len(to_insert),
        warnings=warnings,
    )
