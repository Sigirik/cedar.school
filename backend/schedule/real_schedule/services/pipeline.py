# backend/schedule/real_schedule/services/pipeline.py
# Генерация RealLesson из активной/заданной шаблонной недели + привязка к KTP по дате плана.
# Валидации базовые (длительность>0).
# Пересечения по дате/времени (teacher/grade) проверяем внутри создаваемого набора.

import uuid
import datetime as dt
from datetime import timezone as dt_timezone
from dataclasses import dataclass
from typing import Iterable

from django.apps import apps
from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone

from schedule.real_schedule.models import RealLesson
from schedule.template.models import TemplateWeek, TemplateLesson
from schedule.ktp.models import KTPEntry


@dataclass
class GenerateResult:
    version: int
    generation_batch_id: str
    deleted: int
    created: int
    warnings: list


class CollisionError(Exception):
    """Поднимаем, когда нашли пересечения; details — структурированная диагностика."""
    def __init__(self, details: dict):
        self.details = details
        super().__init__("COLLISIONS_FOUND")


def _active_template_week_id() -> int | None:
    tw = (
        TemplateWeek.objects
        .filter(is_active=True)
        .only("id")
        .order_by("-id")
        .first()
    )
    return tw.id if tw else None


def _iter_dates(d_from: dt.date, d_to: dt.date) -> Iterable[dt.date]:
    cur = d_from
    while cur <= d_to:
        yield cur
        cur += dt.timedelta(days=1)


def _collect_template_lessons_for_range(template_week_id: int, d_from: dt.date, d_to: dt.date):
    """
    Для каждого дня в интервале [from..to] подбираем уроки шаблона по day_of_week.
    Возвращает итератор словарей: {"real_date": date, "template_lesson": tl}
    """
    lessons = list(
        TemplateLesson.objects
        .filter(template_week_id=template_week_id)
        .select_related("subject", "grade", "teacher", "type")
        .order_by("day_of_week", "start_time")
    )

    by_weekday: dict[int, list[TemplateLesson]] = {}
    for tl in lessons:
        by_weekday.setdefault(tl.day_of_week, []).append(tl)

    for date in _iter_dates(d_from, d_to):
        weekday = date.weekday()  # 0 = Monday
        for tl in by_weekday.get(weekday, []):
            yield {"real_date": date, "template_lesson": tl}

def _select_ktp_template_id(grade_id: int, subject_id: int) -> int | None:
    """Авто-детект подходящего KTPTemplate для пары (grade, subject)."""
    KTPTemplate = apps.get_model('ktp','KTPTemplate')
    qs = KTPTemplate.objects.filter(grade_id=grade_id, subject_id=subject_id)

    # если есть флаг активности — приоритизируем
    field_names = {f.name for f in KTPTemplate._meta.get_fields()}
    if 'is_active' in field_names:
        active = list(qs.filter(is_active=True).values_list('id', flat=True))
        if len(active) == 1:
            return active[0]
        elif len(active) > 1:
            # несколько активных — возьмём самый новый
            return max(active)

    # иначе — просто самый новый по id
    last = qs.order_by('-id').values_list('id', flat=True).first()
    return last

def _find_ktp_entry(
    subject_id: int,
    grade_id: int,
    date_: dt.date,
    template_lesson_id: int | None,
    *,
    used_ids: set[int] | None = None,
    ktp_template_id: int | None = None,
):
    KTPEntry = apps.get_model('ktp', 'KTPEntry')

    base = KTPEntry.objects.filter(
        section__ktp_template__grade_id=grade_id,
        section__ktp_template__subject_id=subject_id,
    )

    # уточняем шаблон КТП (либо явно из аргумента, либо авто-детект)
    if ktp_template_id is None:
        ktp_template_id = _select_ktp_template_id(grade_id, subject_id)
    if ktp_template_id is not None:
        base = base.filter(section__ktp_template_id=ktp_template_id)

    if used_ids:
        base = base.exclude(id__in=list(used_ids))

    # 0) жёсткая связка с шаблонным уроком
    if template_lesson_id:
        e = base.filter(template_lesson_id=template_lesson_id).order_by('order').first()
        if e: return e

    # 1) точная дата
    e = base.filter(planned_date=date_).order_by('order').first()
    if e: return e

    # 2) «свободные» (без плановой даты)
    e = base.filter(planned_date__isnull=True).order_by('order').first()
    if e: return e

    # 3) ближайшие по дате
    e = (base.filter(planned_date__gt=date_).order_by('planned_date','order').first()
         or base.filter(planned_date__lt=date_).order_by('-planned_date','order').first())
    return e

def _collect_collisions(new_lessons: list[RealLesson]) -> dict:
    """
    Возвращает подробности пересечений:
    {
      "teacher": [ { "key": [date, teacher_id], "clusters": [ [idx, ...], ... ] , "items": [...] } ],
      "grade":   [ { "key": [date, grade_id],   "clusters": [ [idx, ...], ... ] , "items": [...] } ],
    }
    где items — список по ключу с полями уроков (для диагностики).
    """
    from collections import defaultdict

    def end_for(rl: RealLesson) -> dt.datetime:
        return rl.start + dt.timedelta(minutes=rl.duration_minutes)

    def group(items):
        """items: list[(start, end, idx)] → список кластеров пересечений по индексам."""
        items_sorted = sorted(items, key=lambda x: (x[0], x[1]))
        clusters: list[list[int]] = []
        cur: list[tuple[dt.datetime, dt.datetime, int]] = []
        for it in items_sorted:
            if not cur:
                cur = [it]
                continue
            if it[0] < cur[-1][1]:  # начало раньше конца последнего — пересечение
                cur.append(it)
            else:
                if len(cur) > 1:
                    clusters.append([idx for *_t, idx in cur])
                cur = [it]
        if cur and len(cur) > 1:
            clusters.append([idx for *_t, idx in cur])
        return clusters

    # удобные описания для вывода
    items_desc: list[dict] = []
    for i, rl in enumerate(new_lessons):
        items_desc.append({
            "i": i,
            "date": rl.start.date().isoformat(),
            "start": rl.start.isoformat(),
            "end": (rl.start + dt.timedelta(minutes=rl.duration_minutes)).isoformat(),
            "grade_id": rl.grade_id,
            "teacher_id": rl.teacher_id,
            "subject_id": rl.subject_id,
            "template_lesson_id": rl.template_lesson_id,
        })

    by_teacher = defaultdict(list)  # (date, teacher_id) -> [(start,end,i), ...]
    by_grade   = defaultdict(list)  # (date, grade_id)   -> [(start,end,i), ...]
    for i, rl in enumerate(new_lessons):
        d = rl.start.date()
        by_teacher[(d, rl.teacher_id)].append((rl.start, end_for(rl), i))
        by_grade[(d, rl.grade_id)].append((rl.start, end_for(rl), i))

    def build(coll_map, key_name):
        out = []
        for key, arr in coll_map.items():
            clusters = group(arr)
            if not clusters:
                continue
            key_date, key_id = key
            items = [it for it in items_desc
                     if it[key_name] == key_id and it["date"] == key_date.isoformat()]
            out.append({
                "key": [key_date.isoformat(), key_id],
                "clusters": clusters,
                "items": items,
            })
        return out

    return {
        "teacher": build(coll_map=by_teacher, key_name="teacher_id"),
        "grade":   build(coll_map=by_grade,   key_name="grade_id"),
    }


@transaction.atomic
def generate(
    from_date: dt.date,
    to_date: dt.date,
    template_week_id: int | None = None,
    rewrite_from: dt.date | None = None,
    debug: bool = False,
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

    debug_info = {"template_week_id": template_week_id}

    if rewrite_from is None:
        rewrite_from = from_date

    # Интерпретируем «школьные» даты/время в таймзоне проекта (Europe/Moscow),
    # а храним в БД в UTC (Django выполнит конвертацию при сохранении).
    school_tz = timezone.get_default_timezone()
    rewrite_from_local = timezone.make_aware(
        dt.datetime.combine(rewrite_from, dt.time.min),
        school_tz,
    )
    rewrite_from_utc = rewrite_from_local.astimezone(dt_timezone.utc)

    deleted, _ = RealLesson.objects.filter(
        source=RealLesson.Source.TEMPLATE, start__gte=rewrite_from_utc
    ).delete()

    prev_version = RealLesson.objects.aggregate(m=Max("version"))["m"] or 0
    new_version = prev_version + 1
    batch_id = uuid.uuid4()

    used_ktp_ids: set[int] = set(
        RealLesson.objects.exclude(ktp_entry_id=None).values_list("ktp_entry_id", flat=True)
    )

    # Темы КТП, уже использованные в существующих уроках (вне текущего окна)
    used_ktp_ids: set[int] = set(
        RealLesson.objects.exclude(ktp_entry_id=None).values_list("ktp_entry_id", flat=True)
    )

    # Загружаем уроки шаблона и собираем набор RealLesson
    to_insert: list[RealLesson] = []
    warnings: list[dict] = []

    for item in _collect_template_lessons_for_range(template_week_id, from_date, to_date):
        tl: TemplateLesson = item["template_lesson"]
        date_ = item["real_date"]

        # «Стеночное» время урока берём в таймзоне школы (Europe/Moscow),
        # далее Django сохранит в UTC.
        start_dt = timezone.make_aware(
            dt.datetime.combine(date_, tl.start_time),
            school_tz,
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
        entry = _find_ktp_entry(
            tl.subject_id, tl.grade_id, date_, tl.id,
            used_ids=used_ktp_ids,
            ktp_template_id=None,  # или подставим явно из API (см. ниже)
        )

        if entry:
            rl.ktp_entry_id = entry.id
            rl.topic_order = entry.order
            rl.topic_title = entry.title
            used_ktp_ids.add(entry.id)
        else:
            rl.topic_title = "Тему задаст учитель на уроке"
            warnings.append({
                "code": "KTP_MISS",
                "message": f"Нет KTPEntry для {date_} {tl.grade_id}/{tl.subject_id}",
            })

        if rl.duration_minutes <= 0:
            raise ValueError("MISSING_OR_INVALID_DURATION")

        to_insert.append(rl)

    # Валидации пересечений внутри создаваемого набора
    collisions = _collect_collisions(to_insert)
    if collisions["grade"] or collisions["teacher"]:
        first = (collisions["grade"][0] if collisions["grade"] else collisions["teacher"][0])
        k = first["key"]
        msg = ("OVERLAP_GRADE on (%s, %s)" % (k[0], k[1])) if collisions["grade"] else \
              ("OVERLAP_TEACHER on (%s, %s)" % (k[0], k[1]))
        if debug:
            raise CollisionError({"message": msg, "collisions": collisions, **debug_info})
        raise ValueError(msg)

    # Вставка
    RealLesson.objects.bulk_create(to_insert, batch_size=500)

    return GenerateResult(
        version=new_version,
        generation_batch_id=str(batch_id),
        deleted=deleted,
        created=len(to_insert),
        warnings=warnings,
    )
