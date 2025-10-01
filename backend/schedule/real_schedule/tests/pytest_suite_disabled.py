import datetime as dt
from django.utils import timezone
import pytest
from django.urls import reverse
from schedule.real_schedule.models import RealLesson, Room
from schedule.template.models import TemplateWeek, TemplateLesson
from schedule.ktp.models import KTPEntry, KTPSection, KTPTemplate
from schedule.core.models import Subject, Grade, LessonType
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_generate_creates_lessons(client):
    # Фабрики опусти — быстрый smoke
    subj = Subject.objects.create(name="Мат.")
    grd = Grade.objects.create(name="9А")
    t = User.objects.create(username="t1", role="TEACHER")
    lt = LessonType.objects.create(key="lesson", label="Урок")

    tw = TemplateWeek.objects.create(name="W1", academic_year_id=1, is_active=True)
    TemplateLesson.objects.create(
        template_week=tw, grade=grd, subject=subj, teacher=t,
        day_of_week=0, start_time=dt.time(10,0), duration_minutes=45, type=lt
    )

    # KTP на ту же дату
    ktp = KTPTemplate.objects.create(subject=subj, grade=grd, academic_year_id=1, name="KTP")
    sec = KTPSection.objects.create(ktp_template=ktp, title="S", order=1, hours=1)
    KTPEntry.objects.create(section=sec, order=1, lesson_number=1, title="Тема", planned_date=dt.date(2025,8,25))

    resp = client.post("/api/real-schedule/generate/", data={
        "from": "2025-08-25", "to": "2025-08-25", "template_week_id": tw.id
    }, content_type="application/json")
    assert resp.status_code == 201
    assert RealLesson.objects.count() == 1
    rl = RealLesson.objects.first()
    assert rl.ktp_entry is not None
    assert rl.topic_title == "Тема"

@pytest.mark.django_db
def test_room_end_sets_conducted_and_ktp(client):
    subj = Subject.objects.create(name="Мат.")
    grd = Grade.objects.create(name="9А")
    t = User.objects.create(username="t1", role="TEACHER")
    lt = LessonType.objects.create(key="lesson", label="Урок")
    rl = RealLesson.objects.create(
        subject=subj, grade=grd, teacher=t,
        start=timezone.now(), duration_minutes=45,
        lesson_type=lt, source=RealLesson.Source.TEMPLATE
    )
    ktp = KTPTemplate.objects.create(subject=subj, grade=grd, academic_year_id=1, name="KTP")
    sec = KTPSection.objects.create(ktp_template=ktp, title="S", order=1, hours=1)
    ent = KTPEntry.objects.create(section=sec, order=1, lesson_number=1, title="T")
    rl.ktp_entry = ent; rl.save()

    # create room
    resp = client.post("/api/rooms/get-or-create/", data={"lesson_id": rl.id, "join_url": "https://x"}, content_type="application/json")
    assert resp.status_code in (200, 201)
    room_id = resp.json()["id"]
    # end room
    resp = client.post(f"/api/rooms/{room_id}/end/")
    assert resp.status_code == 200
    rl.refresh_from_db(); ent.refresh_from_db()
    assert rl.conducted_at is not None
    assert ent.actual_date is not None
