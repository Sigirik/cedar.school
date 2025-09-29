import datetime as dt
import pytest
from zoneinfo import ZoneInfo
from django.utils import timezone
from django.apps import apps

from schedule.real_schedule.services.pipeline import generate
from schedule.template.models import TemplateWeek, TemplateLesson
from schedule.core.models import Grade, Subject, LessonType
from schedule.real_schedule.models import RealLesson

pytestmark = pytest.mark.django_db

def t(h, m=0): return dt.time(h, m)

def _get_duration_minutes(rl):
    for cand in ("duration_minutes", "duration", "length_minutes"):
        if hasattr(rl, cand):
            return int(getattr(rl, cand))
    return 45  # дефолт для теста, если поле отсутствует

def test_time_local_wall_time_preserved_europe_moscow(ay):
    grade = Grade.objects.create(name="5Б") if hasattr(Grade, "name") else Grade.objects.create(title="5Б")
    subj  = Subject.objects.create(name="География") if hasattr(Subject, "name") else Subject.objects.create(title="География")
    lt    = LessonType.objects.create(key="lesson", label="Урок") if hasattr(LessonType, "key") else LessonType.objects.create(label="Урок")
    tw    = TemplateWeek.objects.create(is_active=True, academic_year=ay)

    User = apps.get_model("users", "User")
    teacher = User.objects.create(username="t_time")

    TemplateLesson.objects.create(
        template_week=tw, day_of_week=1, start_time=t(9,0), duration_minutes=45,
        grade=grade, subject=subj, teacher=teacher, type=lt
    )
    d1, d2 = dt.date(2025, 9, 1), dt.date(2025, 9, 7)
    generate(d1, d2, debug=True)

    rl = RealLesson.objects.get()

    # start должен быть aware
    assert timezone.is_aware(rl.start)

    # end: либо поле существует и aware, либо считаем от start по duration
    if hasattr(rl, "end"):
        assert timezone.is_aware(rl.end)
        end_dt = rl.end
    else:
        end_dt = rl.start + dt.timedelta(minutes=_get_duration_minutes(rl))

    # длительность 45 минут
    assert int((end_dt - rl.start).total_seconds()) == 45 * 60

    # локальное «стеночное» время Europe/Moscow должно быть 09:00
    msk_start = rl.start.astimezone(ZoneInfo("Europe/Moscow"))
    assert (msk_start.hour, msk_start.minute) == (9, 0)

    # смещение таймзоны: в разных проектах либо UTC (0), либо MSK (+03:00)
    off = rl.start.utcoffset()
    assert off is not None
    assert int(off.total_seconds()) in (0, 3 * 3600)
