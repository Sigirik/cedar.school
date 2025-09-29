# backend/schedule/real_schedule/tests/test_view_as.py
import datetime as dt
import pytest
from rest_framework.test import APIClient
from schedule.real_schedule.tests.test_my_schedule import base_data as base_data
from schedule.real_schedule.tests.test_my_schedule import api as api
API_VIEW_AS = "/api/real_schedule/view_as/{user_id}/"

@pytest.mark.django_db
def test_teacher_cannot_view_foreign_student(api, base_data, monkeypatch):
    users = base_data["users"]
    grades = base_data["grades"]
    subjects = base_data["subjects"]
    lt = base_data["lesson_types"]["lesson"]

    # фиксируем неделю
    from schedule.core.services import date_windows as dw
    monkeypatch.setattr(dw, "get_default_school_week", lambda: (dt.date(2025,9,1), dt.date(2025,9,7)))

    # создаём урок, где ведёт другой учитель (teacher2), а студент — student
    from schedule.real_schedule.models import RealLesson
    from zoneinfo import ZoneInfo
    RealLesson.objects.create(
        subject=subjects["math"], grade=grades["g5a"], teacher=users["teacher2"],
        lesson_type=lt, start=dt.datetime(2025,9,1,8,0,tzinfo=ZoneInfo("UTC")), duration_minutes=45
    )

    api.force_authenticate(users["teacher"])  # teacher НЕ ведёт этого студента
    resp = api.get(API_VIEW_AS.format(user_id=users["student"].id))
    assert resp.status_code == 403

@pytest.mark.django_db
def test_teacher_can_view_own_student(api, base_data, monkeypatch):
    users = base_data["users"]
    grades = base_data["grades"]
    subjects = base_data["subjects"]
    lt = base_data["lesson_types"]["lesson"]

    from schedule.core.services import date_windows as dw
    monkeypatch.setattr(dw, "get_default_school_week", lambda: (dt.date(2025,9,1), dt.date(2025,9,7)))

    from schedule.real_schedule.models import RealLesson
    from zoneinfo import ZoneInfo
    # урок, который ведёт именно этот teacher — студент считается «его»
    RealLesson.objects.create(
        subject=subjects["math"], grade=grades["g5a"], teacher=users["teacher"],
        lesson_type=lt, start=dt.datetime(2025,9,2,8,0,tzinfo=ZoneInfo("UTC")), duration_minutes=45
    )

    api.force_authenticate(users["teacher"])
    resp = api.get(API_VIEW_AS.format(user_id=users["student"].id))
    assert resp.status_code == 200
    body = resp.json()
    assert "results" in body and isinstance(body["results"], list)
