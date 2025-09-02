# tests/test_real_generation_pipeline.py
import pytest
from datetime import date, timedelta, time

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
    """Возвращает дату, которая уже является понедельником (для стабильности теста)."""
    d = date(year, month, day)
    # если не понедельник — докрутим до понедельника той же недели
    return d - timedelta(days=d.weekday())


def _generate(api, d_from: date, d_to: date, debug=True):
    qs = f"?from={d_from.isoformat()}&to={d_to.isoformat()}"
    if debug:
        qs += "&debug=1"
    resp = api.post(f"/api/real_schedule/generate/{qs}")
    return resp


def test_generate_copies_lesson_type_from_template_to_real(api):
    """
    Генерация из активной TemplateWeek переносит type (LessonType) в RealLesson.lesson_type.
    """
    # 1) Справочники и типы
    subject = Subject.objects.create(name="Математика")
    grade   = Grade.objects.create(name="5А")
    lecture = LessonType.objects.create(key="lecture", label="Лекция", counts_towards_norm=True)

    # 2) Преподаватель и авторизация
    teacher = User.objects.create_user(username="t1", password="x", role="TEACHER", is_staff=True)
    # для IsAuthenticated — достаточно force_authenticate
    api.force_authenticate(user=teacher)

    # 3) Шаблон недели и урок в понедельник 09:00
    week = TemplateWeek.objects.create(name="W")
    tl = TemplateLesson.objects.create(
        template_week=week,
        subject=subject,
        grade=grade,
        teacher=teacher,
        day_of_week=0,                 # Monday
        start_time=time(9, 0),
        duration_minutes=45,
        type=lecture,                  # <-- ключевое: тип урока в шаблоне
    )
    ActiveTemplateWeek.objects.create(template=week)

    # 4) Генерация за одну учебную неделю
    monday = _monday_of(2025, 9, 1)    # 2025-09-01 — понедельник
    sunday = monday + timedelta(days=6)

    resp = _generate(api, monday, sunday, debug=True)
    assert resp.status_code == 201, resp.data

    gen_id = resp.data.get("generation_batch_id")
    assert gen_id, resp.data

    # 5) Проверим созданные RealLesson по batch_id
    created = list(RealLesson.objects.filter(generation_batch_id=gen_id))
    assert len(created) >= 1, "Ожидали хотя бы один созданный урок за неделю"

    rl = created[0]
    # FK на тип перенесён
    assert rl.lesson_type_id == lecture.id
    # Остальные поля соответствуют
    assert rl.subject_id == subject.id
    assert rl.grade_id == grade.id
    assert rl.teacher_id == teacher.id
    assert rl.duration_minutes == 45

    # Опциональная связка назад на template_lesson_id (если пайплайн её ставит)
    # Если у тебя поле заполняется — эта проверка пройдёт:
    # Если нет — просто убери/закомментируй.
    if rl.template_lesson_id is not None:
        assert rl.template_lesson_id == tl.id
