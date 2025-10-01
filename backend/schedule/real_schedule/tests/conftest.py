import datetime as dt
import pytest
from django.apps import apps

from schedule.template.models import TemplateWeek, TemplateLesson
from schedule.core.models import Grade, Subject, LessonType


@pytest.fixture
def ay():
    """Создаёт актуальный AcademicYear с валидными датами и возвращает инстанс."""
    AY = apps.get_model("core", "AcademicYear")
    field_names = {f.name for f in AY._meta.fields}

    kwargs = {}
    # name / title
    if "name" in field_names:
        kwargs["name"] = "2025-2026"
    elif "title" in field_names:
        kwargs["title"] = "2025-2026"

    # is_current (если есть)
    if "is_current" in field_names:
        kwargs["is_current"] = True

    start = dt.date(2025, 9, 1)
    end = dt.date(2026, 5, 31)

    # даты (поддержка разных моделей)
    if "start_date" in field_names:
        kwargs["start_date"] = start
    elif "date_start" in field_names:
        kwargs["date_start"] = start
    elif "from_date" in field_names:
        kwargs["from_date"] = start

    if "end_date" in field_names:
        kwargs["end_date"] = end
    elif "date_end" in field_names:
        kwargs["date_end"] = end
    elif "to_date" in field_names:
        kwargs["to_date"] = end

    return AY.objects.create(**kwargs)


@pytest.fixture
def ref(db):
    subj = Subject.objects.create(name="Math") if hasattr(Subject, "name") else Subject.objects.create(title="Math")
    grade = Grade.objects.create(name="9А") if hasattr(Grade, "name") else Grade.objects.create(title="9А")
    teacher_model = apps.get_model("users", "User")
    teacher = teacher_model.objects.create(username="t1")
    lt = LessonType.objects.create(key="lesson", label="Урок") if hasattr(LessonType, "key") \
         else LessonType.objects.create(label="Урок")
    return subj, grade, teacher, lt


@pytest.fixture
def week_with_lessons(db, ay, ref):
    """
    Активная неделя + ТРИ TL (пн/вт/ср), чтобы в интервале пн-вс родилось 3 RealLesson.
    ВАЖНО: teacher не NULL.
    """
    subj, grade, teacher, lt = ref
    tw = TemplateWeek.objects.create(name="W1", academic_year=ay, is_active=True)

    TemplateLesson.objects.create(
        template_week=tw, day_of_week=1, start_time=dt.time(9, 0), duration_minutes=45,
        grade=grade, subject=subj, teacher=teacher, type=lt
    )
    TemplateLesson.objects.create(
        template_week=tw, day_of_week=2, start_time=dt.time(10, 0), duration_minutes=45,
        grade=grade, subject=subj, teacher=teacher, type=lt
    )
    TemplateLesson.objects.create(
        template_week=tw, day_of_week=3, start_time=dt.time(11, 0), duration_minutes=45,
        grade=grade, subject=subj, teacher=teacher, type=lt
    )
    return tw
