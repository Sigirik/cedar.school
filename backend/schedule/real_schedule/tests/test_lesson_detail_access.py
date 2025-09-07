# backend/schedule/real_schedule/tests/test_lesson_detail_access.py
import pytest

@pytest.mark.django_db
def test_student_must_be_subscribed_to_subject(api_client, lesson, student_user_same_grade_not_subscribed):
    api_client.force_authenticate(student_user_same_grade_not_subscribed)
    r = api_client.get(f"/api/lessons/{lesson.id}/")
    assert r.status_code in (403, 401)  # в зависимости от вашей глобальной политики

@pytest.mark.django_db
def test_student_subscribed_can_see(api_client, lesson, student_user_subscribed):
    api_client.force_authenticate(student_user_subscribed)
    r = api_client.get(f"/api/lessons/{lesson.id}/")
    assert r.status_code == 200

@pytest.mark.django_db
def test_parent_child_subscribed_can_see(api_client, lesson, parent_user_with_child_subscribed):
    api_client.force_authenticate(parent_user_with_child_subscribed)
    r = api_client.get(f"/api/lessons/{lesson.id}/")
    assert r.status_code == 200

@pytest.mark.django_db
def test_teacher_not_assigned_is_forbidden_even_if_has_teacher_subject(api_client, lesson, teacher_user_with_subject_but_not_assigned):
    api_client.force_authenticate(teacher_user_with_subject_but_not_assigned)
    r = api_client.get(f"/api/lessons/{lesson.id}/")
    assert r.status_code == 403

@pytest.mark.django_db
def test_students_count_matches_student_subject(api_client, lesson, admin_user, student_subject_factory):
    # создаём N подписок на предмет в этом классе
    n = 3
    for _ in range(n):
        student_subject_factory(grade=lesson.grade, subject=lesson.subject)
    api_client.force_authenticate(admin_user)
    r = api_client.get(f"/api/lessons/{lesson.id}/")
    assert r.status_code == 200
    assert r.data["participants"]["students_count"] == n
