import pytest
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status
from users.models import User
from schedule.core.models import Grade, Subject
from schedule.draft.views import validate_draft
from .conftest import _norm_code

pytestmark = pytest.mark.django_db

def _admin():
    return User.objects.create_superuser(username="admin", password="x")

def test_multi_overlap_cluster_grouping_and_order():
    admin = _admin()
    g = Grade.objects.create(name="5В") if hasattr(Grade, "name") else Grade.objects.create(title="5В")
    subj = Subject.objects.create(name="...")
    payload = {"lessons": [
        {"id": 101, "teacher_id": 77, "grade_id": g.id, "subject_id": subj.id, "room_id": None,
         "day_of_week": 1, "start_time": "09:00", "duration_minutes": 60},
        {"id": 102, "teacher_id": 77, "grade_id": g.id, "subject_id": subj.id, "room_id": None,
         "day_of_week": 1, "start_time": "09:30", "duration_minutes": 45},
        {"id": 110, "teacher_id": 77, "grade_id": g.id, "subject_id": subj.id, "room_id": None,
         "day_of_week": 1, "start_time": "09:45", "duration_minutes": 30},
    ]}
    req = APIRequestFactory().post("/api/draft/template-drafts/validate/", payload, format="json")
    force_authenticate(req, user=admin)
    r = validate_draft(req)
    assert r.status_code == status.HTTP_200_OK
    errs = r.data.get("errors", [])
    buckets = [e for e in errs if _norm_code(e) == "TEACHER_OVERLAP"]
    assert len(buckets) >= 1, r.data
    if len(buckets) == 1 and "lesson_ids" in buckets[0]:
        assert sorted(buckets[0]["lesson_ids"]) == [101, 102, 110]

