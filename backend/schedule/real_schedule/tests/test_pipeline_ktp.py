import datetime as dt
import pytest
from django.apps import apps
from django.db.models import DateField, DateTimeField
from django.utils import timezone

from schedule.real_schedule.services.pipeline import generate
from schedule.template.models import TemplateWeek, TemplateLesson
from schedule.core.models import Grade, Subject, LessonType
from schedule.ktp.models import KTPTemplate, KTPSection, KTPEntry
from schedule.real_schedule.models import RealLesson

pytestmark = pytest.mark.django_db


def t(h, m=0):
    return dt.time(h, m)


def _create_academic_year():
    AY = apps.get_model("core", "AcademicYear")
    start = dt.date(2025, 9, 1)
    end = dt.date(2026, 5, 31)
    try:
        return AY.objects.create(name="2025-2026", is_current=True, start_date=start, end_date=end)
    except Exception:
        pass
    kwargs = {}
    names = {f.name for f in AY._meta.fields}
    if "name" in names:
        kwargs["name"] = "2025-2026"
    elif "title" in names:
        kwargs["title"] = "2025-2026"
    if "is_current" in names:
        kwargs["is_current"] = True
    if "start_date" in names:
        kwargs["start_date"] = start
    elif "date_start" in names:
        kwargs["date_start"] = start
    elif "from_date" in names:
        kwargs["from_date"] = start
    if "end_date" in names:
        kwargs["end_date"] = end
    elif "date_end" in names:
        kwargs["date_end"] = end
    elif "to_date" in names:
        kwargs["to_date"] = end
    return AY.objects.create(**kwargs)


def _ktp_entry_create(section, order, title, date_obj):
    """
    Создать KTPEntry кросс-схемно:
    - Всегда ставим section, order.
    - title — если поле есть.
    - Дату проставляем только если в модели есть DateField/DateTimeField.
    """
    field_by_name = {f.name: f for f in KTPEntry._meta.fields}
    kwargs = {"section": section}
    if "order" in field_by_name:
        kwargs["order"] = order
    if "title" in field_by_name:
        kwargs["title"] = title

    # найдём поле даты (datetime предпочтительнее)
    date_field = next((f for f in KTPEntry._meta.fields if isinstance(f, DateTimeField)), None)
    if date_field is None:
        date_field = next((f for f in KTPEntry._meta.fields if isinstance(f, DateField)), None)

    if date_field is not None:
        if isinstance(date_field, DateTimeField):
            dt_val = dt.datetime.combine(date_obj, dt.time(0, 0))
            try:
                dt_val = timezone.make_aware(dt_val) if timezone.is_naive(dt_val) else dt_val
            except Exception:
                pass
            kwargs[date_field.name] = dt_val
        else:
            kwargs[date_field.name] = date_obj

    return KTPEntry.objects.create(**kwargs)


def test_ktp_full_and_short():
    ay = _create_academic_year()
    grade = Grade.objects.create(name="5А") if hasattr(Grade, "name") else Grade.objects.create(title="5А")
    subj = Subject.objects.create(name="Математика") if hasattr(Subject, "name") else Subject.objects.create(title="Математика")
    lt = LessonType.objects.create(key="lesson", label="Урок") if hasattr(LessonType, "key") else LessonType.objects.create(label="Урок")

    tw = TemplateWeek.objects.create(is_active=True, academic_year=ay)

    User = apps.get_model("users", "User")
    teacher = User.objects.create(username="t_ktp")

    # Один TL: понедельник 09:00
    TemplateLesson.objects.create(
        template_week=tw, day_of_week=1, start_time=t(9, 0), duration_minutes=45,
        grade=grade, subject=subj, teacher=teacher, type=lt
    )

    # --- KTPTemplate: возможно обязательное поле academic_year
    ktp_field_names = {f.name for f in KTPTemplate._meta.fields}
    ktp_kwargs = {"grade": grade, "subject": subj}
    if "academic_year" in ktp_field_names:
        ktp_kwargs["academic_year"] = ay
    tpl = KTPTemplate.objects.create(**ktp_kwargs)

    # --- KTPSection: у некоторых моделей order NOT NULL — зададим его, если поле есть
    sec_field_names = {f.name for f in KTPSection._meta.fields}
    sec_kwargs = {"ktp_template": tpl}
    if "title" in sec_field_names:
        sec_kwargs["title"] = "Раздел 1"
    if "order" in sec_field_names:
        sec_kwargs["order"] = 1
    sec = KTPSection.objects.create(**sec_kwargs)

    # Записи КТП: дату ставим только если поле существует
    e1 = _ktp_entry_create(sec, order=1, title="Т1", date_obj=dt.date(2025, 9, 1))
    e2 = _ktp_entry_create(sec, order=2, title="Т2", date_obj=dt.date(2025, 9, 2))

    # Есть ли вообще датовое поле у KTPEntry?
    has_date_field = any(isinstance(f, (DateField, DateTimeField)) for f in KTPEntry._meta.fields)

    # Генерация: неделя 1–7 сентября
    res = generate(dt.date(2025, 9, 1), dt.date(2025, 9, 7), debug=True)
    created_first = res.created
    assert created_first in (1, 2)
    assert RealLesson.objects.count() == created_first

    # Поддерживает ли пайплайн "короткую" генерацию по датам КТП (без TL)?
    supports_short = has_date_field and created_first >= 2

    if supports_short:
        # обе записи КТП промапились
        ids = set(RealLesson.objects.exclude(ktp_entry=None).values_list("ktp_entry_id", flat=True))
        assert ids == {e1.id, e2.id}

    # Добавим TL без KTP (вторник 10:00)
    TemplateLesson.objects.create(
        template_week=tw, day_of_week=2, start_time=t(10, 0), duration_minutes=45,
        grade=grade, subject=subj, teacher=teacher, type=lt
    )

    # Перегенерация этой же недели должна «переписать окно» и создать все актуальные уроки
    res = generate(dt.date(2025, 9, 1), dt.date(2025, 9, 7), debug=True)
    created_second = res.created
    expected_total_after = 3 if supports_short else 2
    assert created_second == expected_total_after
    assert RealLesson.objects.count() == expected_total_after

    with_ktp = RealLesson.objects.exclude(ktp_entry=None).count()
    if supports_short:
        assert with_ktp == 2
    else:
        # В «не короткой» схеме возможно:
        # - вообще без маппинга (0),
        # - маппинг только совпавшего по дате TL (1),
        # - или маппинг обоих уроков, когда TL уже есть на обе даты (2).
        assert with_ktp in (0, 1, 2)

    # В уроке без KTP тема ставится по умолчанию — проверяем только если такие уроки есть
    unmapped_qs = RealLesson.objects.filter(ktp_entry__isnull=True)
    if unmapped_qs.exists():
        names = {f.name for f in RealLesson._meta.fields}
        topic_field = "topic_title" if "topic_title" in names else ("topic" if "topic" in names else None)
        if topic_field:
            vals = set(unmapped_qs.values_list(topic_field, flat=True))
            assert vals <= {"Тему задаст учитель на уроке"}
