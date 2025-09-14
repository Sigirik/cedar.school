# schedule/real_schedule/tests/test_lessons_list.py
import datetime as dt
import pytest
from zoneinfo import ZoneInfo

from schedule.real_schedule.models import RealLesson

# берём готовые фикстуры/хелперы из test_my_schedule
from schedule.real_schedule.tests.test_my_schedule import (
    api as api,
    base_data as base_data,
    _patch_default_week,
    _create_lesson,
    _aware_utc,
)

API_URL = "/api/real_schedule/lessons/"

@pytest.mark.django_db
def test_lessons_requires_manager_role__403(api, base_data, monkeypatch):
    users = base_data["users"]

    d_from, d_to = dt.date(2025, 9, 1), dt.date(2025, 9, 7)
    _patch_default_week(monkeypatch, d_from, d_to)

    api.force_authenticate(users["student"])  # неуправленец
    resp = api.get(f"{API_URL}?from={d_from.isoformat()}&to={d_to.isoformat()}")
    assert resp.status_code == 403

@pytest.mark.django_db
def test_lessons_filters_and_pagination(api, base_data, monkeypatch):
    users = base_data["users"]
    grades = base_data["grades"]
    subjects = base_data["subjects"]
    lt = base_data["lesson_types"]["lesson"]

    d_from, d_to = dt.date(2025, 9, 1), dt.date(2025, 9, 7)
    _patch_default_week(monkeypatch, d_from, d_to)

    # создаём в окне 3 урока для teacher, 1 для teacher2, 1 вне окна
    _create_lesson(subjects["math"], grades["g5a"], users["teacher"],  lt, _aware_utc(2025, 9, 1,  8))
    _create_lesson(subjects["rus"],  grades["g5a"], users["teacher"],  lt, _aware_utc(2025, 9, 2,  9))
    _create_lesson(subjects["math"], grades["g4a"], users["teacher"],  lt, _aware_utc(2025, 9, 3, 10))
    _create_lesson(subjects["math"], grades["g4a"], users["teacher2"], lt, _aware_utc(2025, 9, 4, 11))
    _create_lesson(subjects["math"], grades["g5a"], users["teacher"],  lt, _aware_utc(2025, 8, 30,  8))  # вне окна

    api.force_authenticate(users["admin"])  # управленец
    # фильтр по teacher_id и page_size=2
    resp = api.get(
        f"{API_URL}?from={d_from.isoformat()}&to={d_to.isoformat()}&teacher_id={users['teacher'].id}&page_size=2"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "count" in body and "results" in body
    # 3 урока учителя в окне → первая страница содержит 2
    assert body["count"] == 3
    assert len(body["results"]) == 2
    assert body["next"] is not None  # есть вторая страница

    # проверим сортировку по возрастанию start, затем grade__name
    times = [item["start_time"] for item in body["results"]]
    assert times == sorted(times)

@pytest.mark.django_db
def test_lessons_invalid_range_400(api, base_data):
    users = base_data["users"]
    api.force_authenticate(users["admin"])
    # диапазон шире 31 дня → 400
    resp = api.get(f"{API_URL}?from=2025-09-01&to=2025-10-15")
    assert resp.status_code == 400
    body = resp.json()
    assert "detail" in body
