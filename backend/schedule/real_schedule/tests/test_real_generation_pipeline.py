# tests/test_real_generation_pipeline.py
import pytest
from datetime import date, timedelta, time

from django.apps import apps
from django.db import models as djm
from rest_framework.test import APIClient

from schedule.core.models import LessonType, Subject, Grade
from schedule.template.models import TemplateWeek, TemplateLesson, ActiveTemplateWeek
from schedule.real_schedule.models import RealLesson
from users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def api():
    return APIClient()


def _monday_of(year, month, day):
    d = date(year, month, day)
    return d - timedelta(days=d.weekday())


def _create_academic_year() -> object:
    AY = apps.get_model("core", "AcademicYear")
    fields = {f.name: f for f in AY._meta.fields if f.editable and not f.auto_created}

    data = {}
    if "name" in fields:
        data["name"] = "2025/26"

    for nm in ("starts_on", "start_on", "start_date", "start"):
        if nm in fields:
            data[nm] = date(2025, 9, 1)
            break
    for nm in ("ends_on", "end_on", "end_date", "end"):
        if nm in fields:
            data[nm] = date(2026, 6, 30)
            break

    for f in fields.values():
        if f.name in data or f.primary_key:
            continue
        if not f.null and f.default is djm.NOT_PROVIDED:
            if isinstance(f, djm.CharField):
                data[f.name] = "x"
            elif isinstance(f, djm.IntegerField):
                data[f.name] = 1
            elif isinstance(f, djm.BooleanField):
                data[f.name] = False
            elif isinstance(f, djm.DateField):
                data[f.name] = date(2025, 9, 1)

    return AY.objects.create(**data)


def _generate(api, d_from: date, d_to: date, week_id: int | None = None, debug=True):
    qs = f"?from={d_from.isoformat()}&to={d_to.isoformat()}"
    if debug:
        qs += "&debug=1"
    if week_id:
        qs += f"&template_week_id={week_id}"   # ← ДОБАВЛЕНО: явный источник шаблона
    return api.post(f"/api/real_schedule/generate/{qs}")


def test_generate_copies_lesson_type_from_template_to_real(api):
    subject = Subject.objects.create(name="Математика")
    grade   = Grade.objects.create(name="5А")
    lecture = LessonType.objects.create(key="lecture", label="Лекция", counts_towards_norm=True)

    teacher = User.objects.create_user(username="t1", password="x", role="TEACHER", is_staff=True)
    api.force_authenticate(user=teacher)

    ay = _create_academic_year()

    week = TemplateWeek.objects.create(name="W", academic_year=ay)
    tl = TemplateLesson.objects.create(
        template_week=week,
        subject=subject,
        grade=grade,
        teacher=teacher,
        day_of_week=0,
        start_time=time(9, 0),
        duration_minutes=45,
        type=lecture,
    )
    ActiveTemplateWeek.objects.create(template=week)  # можно оставить; ключевое — param ниже

    monday = _monday_of(2025, 9, 1)
    sunday = monday + timedelta(days=6)

    resp = _generate(api, monday, sunday, week_id=week.id, debug=True)  # ← ПЕРЕДАЁМ template_week_id
    assert resp.status_code == 201, resp.data

    gen_id = resp.data.get("generation_batch_id")
    assert gen_id, resp.data

    created = list(RealLesson.objects.filter(generation_batch_id=gen_id))
    assert len(created) >= 1, "Ожидали хотя бы один созданный урок за неделю"

    rl = created[0]
    assert rl.lesson_type_id == lecture.id
    assert rl.subject_id == subject.id
    assert rl.grade_id == grade.id
    assert rl.teacher_id == teacher.id
    assert rl.duration_minutes == 45

    if rl.template_lesson_id is not None:
        assert rl.template_lesson_id == tl.id
