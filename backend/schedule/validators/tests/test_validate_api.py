import pytest
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from users.models import User
from schedule.core.models import Grade, Subject, LessonType
from schedule.draft.views import validate_draft  # ← вызываем вьюху напрямую
from .conftest import _norm_code

pytestmark = pytest.mark.django_db

def _mk_admin():
    return User.objects.create_superuser(username="admin", password="Ced@rAdm1n")

def _mk_ref():
    grade = Grade.objects.create(name="5А") if hasattr(Grade, "name") else Grade.objects.create(title="5А")
    subj  = Subject.objects.create(name="Math") if hasattr(Subject, "name") else Subject.objects.create(title="Math")
    lt    = LessonType.objects.create(key="lesson", label="Урок") if hasattr(LessonType, "key") else LessonType.objects.create(label="Урок")
    return grade, subj, lt

def test_validate_api_smoke_empty():
    admin = _mk_admin()
    grade, subj, lt = _mk_ref()
    teacher = User.objects.create(username="t1")

    factory = APIRequestFactory()
    payload = {
        "lessons": [
            {"id": 1, "teacher_id": teacher.id, "grade_id": grade.id, "subject_id": subj.id, "room_id": None,
             "day_of_week": 1, "start_time": "09:00", "duration_minutes": 45},
            {"id": 2, "teacher_id": teacher.id, "grade_id": grade.id, "subject_id": subj.id, "room_id": None,
             "day_of_week": 1, "start_time": "09:45", "duration_minutes": 45},
        ]
    }
    req = factory.post("/api/draft/template-drafts/validate/", payload, format="json")
    force_authenticate(req, user=admin)
    resp = validate_draft(req)

    assert resp.status_code == status.HTTP_200_OK
    data = resp.data
    assert "errors" in data and "warnings" in data
    assert data["errors"] == [] and data["warnings"] == []

def test_validate_api_teacher_overlap_shape():
    admin = _mk_admin()
    grade, subj, lt = _mk_ref()
    teacher = User.objects.create(username="t2")

    factory = APIRequestFactory()
    payload = {
        "lessons": [
            {"id": 1, "teacher_id": teacher.id, "grade_id": grade.id, "subject_id": subj.id, "room_id": None,
             "day_of_week": 2, "start_time": "09:00", "duration_minutes": 45},
            {"id": 2, "teacher_id": teacher.id, "grade_id": grade.id, "subject_id": subj.id, "room_id": None,
             "day_of_week": 2, "start_time": "09:30", "duration_minutes": 45},
        ]
    }
    req = factory.post("/api/draft/template-drafts/validate/", payload, format="json")
    force_authenticate(req, user=admin)
    resp = validate_draft(req)

    assert resp.status_code == status.HTTP_200_OK
    obj = resp.data
    errs = obj.get("errors", [])
    assert any(_norm_code(e) == "TEACHER_OVERLAP" for e in errs), errs
    bucket = next((e for e in errs if _norm_code(e) == "TEACHER_OVERLAP"), None)
    if bucket and "lesson_ids" in bucket:
        assert sorted(bucket["lesson_ids"]) == [1, 2]
