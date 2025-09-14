# schedule/real_schedule/tests/test_my_schedule.py
import datetime as dt
from zoneinfo import ZoneInfo

import pytest
from django.utils.timezone import make_aware
from rest_framework.test import APIClient

from users.models import User, ParentChild
from schedule.core.models import Subject, Grade, LessonType, StudentSubject
from schedule.real_schedule.models import RealLesson


API_URL = "/api/real_schedule/my/"
TST_PREFIX = "tst_my_sched_"


@pytest.fixture
def api() -> APIClient:
    return APIClient()


def _aware_utc(y, m, d, hh, mm=0):
    return make_aware(dt.datetime(y, m, d, hh, mm, 0), dt.timezone.utc)


def _local_hhmmss(utc_dt, tz="Europe/Moscow"):
    return utc_dt.astimezone(ZoneInfo(tz)).strftime("%H:%M:%S")


def _create_lesson(subject, grade, teacher, lesson_type, start_utc, duration=45, **kwargs):
    return RealLesson.objects.create(
        subject=subject,
        grade=grade,
        teacher=teacher,
        lesson_type=lesson_type,
        start=start_utc,
        duration_minutes=duration,
        **kwargs,
    )


def _patch_default_week(monkeypatch, d_from, d_to):
    import schedule.core.services.date_windows as dw
    monkeypatch.setattr(dw, "get_default_school_week", lambda: (d_from, d_to))


@pytest.fixture
def base_data(db):
    """
    База для тестов + явная уборка после каждого теста.
    Работает без поля user.grade — используем StudentSubject.
    """
    # --- create ---
    math = Subject.objects.create(name=f"{TST_PREFIX}Математика")
    rus = Subject.objects.create(name=f"{TST_PREFIX}Русский язык")
    g4a = Grade.objects.create(name=f"{TST_PREFIX}4А")
    g5a = Grade.objects.create(name=f"{TST_PREFIX}5А")
    lt_lesson = LessonType.objects.create(key="lesson", label=f"{TST_PREFIX}Урок")

    admin = User.objects.create_user(username=f"{TST_PREFIX}admin1", password="pass", role=User.Role.ADMIN)
    zavuch = User.objects.create_user(username=f"{TST_PREFIX}zavuch1", password="pass", role=User.Role.HEAD_TEACHER)
    teacher = User.objects.create_user(username=f"{TST_PREFIX}teach1", password="pass", role=User.Role.TEACHER)
    teacher2 = User.objects.create_user(username=f"{TST_PREFIX}teach2", password="pass", role=User.Role.TEACHER)
    parent = User.objects.create_user(username=f"{TST_PREFIX}parent1", password="pass", role=User.Role.PARENT)

    # два студента в режиме индивидуальных предметов
    student = User.objects.create_user(
        username=f"{TST_PREFIX}student1", password="pass",
        role=User.Role.STUDENT, individual_subjects_enabled=True
    )
    student2 = User.objects.create_user(
        username=f"{TST_PREFIX}student2", password="pass",
        role=User.Role.STUDENT, individual_subjects_enabled=True
    )

    # индивидуальные предметы
    StudentSubject.objects.create(student=student, subject=math, grade=g5a)
    StudentSubject.objects.create(student=student, subject=rus, grade=g5a)
    StudentSubject.objects.create(student=student2, subject=math, grade=g4a)

    # родитель → дети
    ParentChild.objects.create(parent=parent, child=student, is_active=True)
    ParentChild.objects.create(parent=parent, child=student2, is_active=True)

    data = dict(
        subjects=dict(math=math, rus=rus),
        grades=dict(g4a=g4a, g5a=g5a),
        lesson_types=dict(lesson=lt_lesson),
        users=dict(
            admin=admin, zavuch=zavuch, teacher=teacher, teacher2=teacher2,
            parent=parent, student=student, student2=student2
        ),
    )

    yield data

    # --- teardown ---
    RealLesson.objects.filter(grade__name__startswith=TST_PREFIX).delete()
    ParentChild.objects.filter(parent__username__startswith=TST_PREFIX).delete()
    StudentSubject.objects.filter(student__username__startswith=TST_PREFIX).delete()
    User.objects.filter(username__startswith=TST_PREFIX).delete()
    LessonType.objects.filter(label__startswith=TST_PREFIX).delete()
    Grade.objects.filter(name__startswith=TST_PREFIX).delete()
    Subject.objects.filter(name__startswith=TST_PREFIX).delete()


@pytest.mark.django_db
def test_admin_gets_all_lessons_default_week(api, base_data, monkeypatch):
    users = base_data["users"]
    grades = base_data["grades"]
    subjects = base_data["subjects"]
    lt = base_data["lesson_types"]["lesson"]

    d_from, d_to = dt.date(2025, 9, 1), dt.date(2025, 9, 7)
    _patch_default_week(monkeypatch, d_from, d_to)

    l1 = _create_lesson(subjects["math"], grades["g5a"], users["teacher"], lt, _aware_utc(2025, 9, 1, 8))
    _create_lesson(subjects["rus"],  grades["g5a"], users["teacher"],  lt, _aware_utc(2025, 9, 2, 9))
    _create_lesson(subjects["math"], grades["g4a"], users["teacher2"], lt, _aware_utc(2025, 9, 3, 10))
    _create_lesson(subjects["math"], grades["g4a"], users["teacher"],  lt, _aware_utc(2025, 8, 30, 8))  # вне окна

    api.force_authenticate(users["admin"])
    resp = api.get(API_URL)
    assert resp.status_code == 200
    body = resp.json()
    assert body["from"] == d_from.isoformat()
    assert body["to"] == d_to.isoformat()
    assert body["count"] == 3

    item = body["results"][0]
    # Проверяем стандартный формат (реалка → date + start_time)
    assert set(item.keys()) >= {"id", "subject", "grade", "teacher", "date", "start_time", "duration_minutes", "type"}
    assert "start" not in item and "day_of_week" not in item
    assert item["date"] == "2025-09-01"
    assert item["start_time"] == _local_hhmmss(l1.start)


@pytest.mark.django_db
def test_teacher_sees_only_own_lessons(api, base_data):
    users = base_data["users"]
    grades = base_data["grades"]
    subjects = base_data["subjects"]
    lt = base_data["lesson_types"]["lesson"]

    _create_lesson(subjects["math"], grades["g5a"], users["teacher"],  lt, _aware_utc(2025, 9, 1, 8))
    _create_lesson(subjects["rus"],  grades["g5a"], users["teacher2"], lt, _aware_utc(2025, 9, 1, 9))

    api.force_authenticate(users["teacher"])
    resp = api.get(f"{API_URL}?from=2025-09-01&to=2025-09-07")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert all(item["teacher"] == users["teacher"].id for item in body["results"])


@pytest.mark.django_db
def test_student_individual_subjects_filter(api, base_data):
    users = base_data["users"]
    grades = base_data["grades"]
    subjects = base_data["subjects"]
    lt = base_data["lesson_types"]["lesson"]

    # студент имеет индивидуальные предметы: math + rus
    _create_lesson(subjects["math"], grades["g5a"], users["teacher"],  lt, _aware_utc(2025, 9, 2, 9))
    _create_lesson(subjects["rus"],  grades["g4a"], users["teacher"],  lt, _aware_utc(2025, 9, 2, 10))
    # лишний предмет, которого нет у студента
    other = Subject.objects.create(name=f"{TST_PREFIX}Чтение")
    _create_lesson(other, grades["g4a"], users["teacher"], lt, _aware_utc(2025, 9, 2, 11))

    api.force_authenticate(users["student"])
    resp = api.get(f"{API_URL}?from=2025-09-01&to=2025-09-07")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    allowed_subjects = {base_data["subjects"]["math"].id, base_data["subjects"]["rus"].id}
    assert all(item["subject"] in allowed_subjects for item in body["results"])


@pytest.mark.django_db
def test_parent_with_children_param(api, base_data):
    users = base_data["users"]
    grades = base_data["grades"]
    subjects = base_data["subjects"]
    lt = base_data["lesson_types"]["lesson"]
    parent = users["parent"]
    child1 = users["student"]
    child2 = users["student2"]

    # уроки на неделю
    _create_lesson(subjects["math"], grades["g5a"], users["teacher"],  lt, _aware_utc(2025, 9, 3, 8))
    _create_lesson(subjects["rus"],  grades["g4a"], users["teacher2"], lt, _aware_utc(2025, 9, 3, 9))

    api.force_authenticate(parent)

    # без children — агрегировано по всем активным детям, просто проверим 200 и не пусто
    resp = api.get(f"{API_URL}?from=2025-09-01&to=2025-09-07")
    assert resp.status_code == 200
    assert resp.json()["count"] >= 1

    # с children=child1 — сузили выборку (важно, что бек не падает)
    resp2 = api.get(f"{API_URL}?from=2025-09-01&to=2025-09-07&children={child1.id}")
    assert resp2.status_code == 200
    assert resp2.json()["count"] >= 1


@pytest.mark.django_db
def test_invalid_date_returns_400(api, base_data):
    api.force_authenticate(base_data["users"]["admin"])
    resp = api.get(f"{API_URL}?from=oops&to=2025-09-07")
    assert resp.status_code == 400
    assert "detail" in resp.json()


@pytest.mark.django_db
def test_too_wide_range_returns_400(api, base_data):
    api.force_authenticate(base_data["users"]["admin"])
    resp = api.get(f"{API_URL}?from=2025-09-01&to=2025-12-31")
    assert resp.status_code == 400
    assert "detail" in resp.json()
