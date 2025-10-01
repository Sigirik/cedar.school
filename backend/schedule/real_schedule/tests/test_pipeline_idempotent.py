import datetime as dt
import pytest
from django.apps import apps

from schedule.real_schedule.services.pipeline import generate
from schedule.template.models import TemplateWeek, TemplateLesson
from schedule.core.models import Grade, Subject, LessonType
from schedule.real_schedule.models import RealLesson

pytestmark = pytest.mark.django_db

def t(h, m=0): import datetime as _dt; return _dt.time(h, m)

def test_generate_is_idempotent_rewrite_window(ay):
    grade = Grade.objects.create(name="5А") if hasattr(Grade, "name") else Grade.objects.create(title="5А")
    subj  = Subject.objects.create(name="Русский") if hasattr(Subject, "name") else Subject.objects.create(title="Русский")
    lt    = LessonType.objects.create(key="lesson", label="Урок") if hasattr(LessonType, "key") else LessonType.objects.create(label="Урок")
    tw    = TemplateWeek.objects.create(is_active=True, academic_year=ay)

    User = apps.get_model("users", "User")
    teacher = User.objects.create(username="t_idem")

    TemplateLesson.objects.create(template_week=tw, day_of_week=1, start_time=t(9), duration_minutes=45,
                                  grade=grade, subject=subj, teacher=teacher, type=lt)

    d1, d2 = dt.date(2025, 9, 1), dt.date(2025, 9, 7)
    res1 = generate(d1, d2, debug=True)
    res2 = generate(d1, d2, debug=True)

    assert RealLesson.objects.count() == res2.created
    starts = list(RealLesson.objects.values_list("start", flat=True))
    assert len(starts) == len(set(starts))
