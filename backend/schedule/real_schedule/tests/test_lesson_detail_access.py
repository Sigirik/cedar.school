import datetime as dt
import pytest
from django.urls import reverse
from django.utils.timezone import make_aware
from rest_framework.test import APIClient
from django.apps import apps

from users.models import User, ParentChild
from schedule.core.models import Subject, Grade, LessonType, StudentSubject
from schedule.real_schedule.models import RealLesson


def detail_url(lesson_id: int) -> str:
    return reverse("lesson-detail", kwargs={"id": lesson_id})


@pytest.fixture
def api() -> APIClient:
    return APIClient()


def _aware_utc(y, m, d, hh, mm=0):
    return make_aware(dt.datetime(y, m, d, hh, mm, 0), dt.timezone.utc)


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


@pytest.fixture
def base_data(db):
    """
    Минимальная база для проверки детальной страницы урока.
    Подход идентичен test_my_schedule.py: локальные фикстуры и прямые создания. 
    """
    # Справочники
    subj = Subject.objects.create(name="Math") if hasattr(Subject, "name") else Subject.objects.create(title="Math")
    grade = Grade.objects.create(name="5A") if hasattr(Grade, "name") else Grade.objects.create(title="5A")
    lt = LessonType.objects.create(key="lesson", label="Урок") if hasattr(LessonType, "key") else LessonType.objects.create(label="Урок")

    # Пользователи
    admin = User.objects.create_user(username="t_admin", password="pass", role=User.Role.ADMIN)
    head  = User.objects.create_user(username="t_head",  password="pass", role=User.Role.HEAD_TEACHER)
    dir_  = User.objects.create_user(username="t_dir",   password="pass", role=User.Role.DIRECTOR)
    t1    = User.objects.create_user(username="t_t1",    password="pass", role=User.Role.TEACHER)
    t2    = User.objects.create_user(username="t_t2",    password="pass", role=User.Role.TEACHER)
    p1    = User.objects.create_user(username="t_parent", password="pass", role=User.Role.PARENT)

    s1    = User.objects.create_user(username="t_s1", password="pass", role=User.Role.STUDENT, individual_subjects_enabled=True)
    s2    = User.objects.create_user(username="t_s2", password="pass", role=User.Role.STUDENT, individual_subjects_enabled=True)

    # Родитель → дети
    ParentChild.objects.create(parent=p1, child=s1, is_active=True)
    ParentChild.objects.create(parent=p1, child=s2, is_active=True)

    # Один урок в 2025-09-02 09:00 UTC
    lesson = _create_lesson(subj, grade, t1, lt, _aware_utc(2025, 9, 2, 9))

    return dict(
        subj=subj, grade=grade, lt=lt,
        users=dict(admin=admin, head=head, dir=dir_, t1=t1, t2=t2, p1=p1, s1=s1, s2=s2),
        lesson=lesson
    )


# --------------------------
# Тесты доступов и контента
# --------------------------

@pytest.mark.django_db
def test_student_must_be_subscribed_to_subject(api, base_data):
    u = base_data["users"]
    lesson = base_data["lesson"]

    # У студента НЕТ подписки на предмет этого урока
    api.force_authenticate(u["s1"])
    r = api.get(detail_url(lesson.id))
    assert r.status_code == 403  # нет прав


@pytest.mark.django_db
def test_student_subscribed_can_see(api, base_data):
    u = base_data["users"]
    lesson = base_data["lesson"]

    # Дадим подписку на предмет/класс урока
    StudentSubject.objects.create(student=u["s1"], subject=base_data["subj"], grade=base_data["grade"])

    api.force_authenticate(u["s1"])
    r = api.get(detail_url(lesson.id))
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == lesson.id
    assert body["subject"] == base_data["subj"].id
    assert body["grade"] == base_data["grade"].id
    assert body["teacher"] == u["t1"].id
    assert "students" in body


@pytest.mark.django_db
def test_parent_child_subscribed_can_see(api, base_data):
    u = base_data["users"]
    lesson = base_data["lesson"]

    # Подписка ребёнка на предмет/класс
    StudentSubject.objects.create(student=u["s1"], subject=base_data["subj"], grade=base_data["grade"])

    api.force_authenticate(u["p1"])
    r = api.get(detail_url(lesson.id))
    assert r.status_code == 200
    # проверим, что вернулись только дети родителя
    ids = [row["id"] for row in r.json()["students"]]
    assert set(ids).issubset({u["s1"].id, u["s2"].id})


@pytest.mark.django_db
def test_teacher_not_assigned_is_forbidden_even_if_has_teacher_subject(api, base_data):
    u = base_data["users"]
    lesson = base_data["lesson"]

    # Учитель НЕ назначен на урок (назначен t1), даже если у него есть "TeacherSubject" — доступ запрещён.
    api.force_authenticate(u["t2"])
    r = api.get(detail_url(lesson.id))
    assert r.status_code == 403


@pytest.mark.django_db
def test_students_count_matches_student_subject(api, base_data):
    u = base_data["users"]; lesson = base_data["lesson"]; subj = base_data["subj"]; grade = base_data["grade"]

    # Создадим 3 подписки на предмет/класс
    extra1 = User.objects.create_user(username="t_s3", password="pass", role=User.Role.STUDENT)
    extra2 = User.objects.create_user(username="t_s4", password="pass", role=User.Role.STUDENT)
    StudentSubject.objects.create(student=u["s1"], subject=subj, grade=grade)
    StudentSubject.objects.create(student=extra1, subject=subj, grade=grade)
    StudentSubject.objects.create(student=extra2, subject=subj, grade=grade)

    api.force_authenticate(u["admin"])
    r = api.get(detail_url(lesson.id))
    assert r.status_code == 200
    assert r.json()["participants"]["students_count"] == 3


@pytest.mark.django_db
def test_teacher_sees_all_students_list(api, base_data):
    u = base_data["users"]; lesson = base_data["lesson"]; subj = base_data["subj"]; grade = base_data["grade"]

    # Подпишем троих на предмет/класс
    extra1 = User.objects.create_user(username="t_s5", password="pass", role=User.Role.STUDENT)
    extra2 = User.objects.create_user(username="t_s6", password="pass", role=User.Role.STUDENT)
    StudentSubject.objects.create(student=u["s1"], subject=subj, grade=grade)
    StudentSubject.objects.create(student=extra1, subject=subj, grade=grade)
    StudentSubject.objects.create(student=extra2, subject=subj, grade=grade)

    api.force_authenticate(u["t1"])  # учитель урока
    r = api.get(detail_url(lesson.id))
    assert r.status_code == 200
    assert len(r.json()["students"]) == 3
    sample = r.json()["students"][0]
    for key in ("id", "first_name", "last_name", "fio", "attendance", "mark"):
        assert key in sample
    for key in ("status", "late_minutes", "display"):
        assert key in sample["attendance"]


@pytest.mark.django_db
def test_student_sees_only_self(api, base_data):
    u = base_data["users"]; lesson = base_data["lesson"]; subj = base_data["subj"]; grade = base_data["grade"]

    # Подпишем троих, среди них текущий студент
    extra1 = User.objects.create_user(username="t_s7", password="pass", role=User.Role.STUDENT)
    StudentSubject.objects.create(student=u["s1"], subject=subj, grade=grade)
    StudentSubject.objects.create(student=extra1, subject=subj, grade=grade)

    api.force_authenticate(u["s1"])
    r = api.get(detail_url(lesson.id))
    assert r.status_code == 200
    ids = [s["id"] for s in r.json()["students"]]
    assert ids == [u["s1"].id]  # только сам


@pytest.mark.django_db
def test_parent_sees_only_children(api, base_data):
    u = base_data["users"]; lesson = base_data["lesson"]; subj = base_data["subj"]; grade = base_data["grade"]

    # Подпишем двоих детей родителя и одного «чужого»
    other = User.objects.create_user(username="t_other", password="pass", role=User.Role.STUDENT)
    StudentSubject.objects.create(student=u["s1"], subject=subj, grade=grade)
    StudentSubject.objects.create(student=u["s2"], subject=subj, grade=grade)
    StudentSubject.objects.create(student=other,  subject=subj, grade=grade)

    api.force_authenticate(u["p1"])
    r = api.get(detail_url(lesson.id))
    assert r.status_code == 200
    returned_ids = {s["id"] for s in r.json()["students"]}
    child_ids = {u["s1"].id, u["s2"].id}
    assert returned_ids.issubset(child_ids)
    assert returned_ids  # не пусто


@pytest.mark.django_db
def test_attendance_display_for_late(api, base_data):
    """
    Скипаем, если модель LessonStudent ещё не добавлена.
    """
    LessonStudent = None
    try:
        LessonStudent = apps.get_model("real_schedule", "LessonStudent")
    except LookupError:
        pytest.skip("Модель LessonStudent отсутствует — пропускаем тест посещаемости.")

    u = base_data["users"]; lesson = base_data["lesson"]; subj = base_data["subj"]; grade = base_data["grade"]

    # Подписанный студент + запись опоздания 7 мин
    StudentSubject.objects.create(student=u["s1"], subject=subj, grade=grade)
    LessonStudent.objects.create(lesson=lesson, student=u["s1"], status="late", late_minutes=7)

    api.force_authenticate(u["admin"])
    r = api.get(detail_url(lesson.id))
    assert r.status_code == 200
    row = next(s for s in r.json()["students"] if s["id"] == u["s1"].id)
    assert row["attendance"]["status"] == "late"
    assert row["attendance"]["late_minutes"] == 7
    assert row["attendance"]["display"] == "опоздание 7 мин"
