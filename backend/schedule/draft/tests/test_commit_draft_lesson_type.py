import json
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from schedule.core.models import LessonType
from schedule.draft.models import TemplateWeekDraft
from schedule.template.models import TemplateWeek, TemplateLesson

def _mk_admin():
    return User.objects.create_superuser(username="admin", password="admin")

def _mk_types():
    LessonType.objects.create(key="lecture", label="Лекция", counts_towards_norm=True)
    LessonType.objects.create(key="lab",     label="Лабораторная", counts_towards_norm=True)

def _mk_draft_with_lesson(type_payload):
    # Черновик с одним уроком; структура подстройте к своей, но принцип такой:
    data = {
        "lessons": [
            {
                "subject": 1, "grade": 1, "teacher": 1,
                "day_of_week": 0, "start_time": "09:00", "duration_minutes": 45,
                "type": type_payload
            }
        ]
    }
    return TemplateWeekDraft.objects.create(data=data)

def _commit(client, draft_id):
    url = f"/api/draft/template-drafts/{draft_id}/commit/"
    return client.post(url, data={}, format="json")

def test_commit_maps_type_by_key(db):
    _mk_types()
    admin = _mk_admin()
    draft = _mk_draft_with_lesson({"key": "lecture"})

    client = APIClient()
    client.force_authenticate(user=admin)

    resp = _commit(client, draft.id)
    assert resp.status_code == status.HTTP_200_OK, resp.data

    # Проверяем, что в активной неделе появился урок с корректным типом
    tl = TemplateLesson.objects.first()
    assert tl is not None
    assert tl.lesson_type.key == "lecture"

def test_commit_maps_type_by_label(db):
    _mk_types()
    admin = _mk_admin()
    draft = _mk_draft_with_lesson({"label": "Лабораторная"})

    client = APIClient()
    client.force_authenticate(user=admin)

    resp = _commit(client, draft.id)
    assert resp.status_code == status.HTTP_200_OK, resp.data
    tl = TemplateLesson.objects.first()
    assert tl.lesson_type.label == "Лабораторная"

def test_commit_unknown_type_returns_400(db):
    _mk_types()
    admin = _mk_admin()
    draft = _mk_draft_with_lesson({"key": "unknown_type"})

    client = APIClient()
    client.force_authenticate(user=admin)

    resp = _commit(client, draft.id)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    # Структура ошибки — как в сервисе
    err = resp.json()
    assert "type" in err
    assert "available" in err["type"]
    assert any(x["key"] == "lecture" for x in err["type"]["available"])
