import datetime as dt
import pytest
from django.apps import apps

from schedule.real_schedule.services.pipeline import generate
from schedule.template.models import TemplateWeek, TemplateLesson
from schedule.core.models import Grade, Subject, LessonType
from schedule.real_schedule.models import RealLesson

pytestmark = pytest.mark.django_db

def t(h, m=0): import datetime as _dt; return _dt.time(h, m)

@pytest.mark.slow
def test_perf_sanity_bulk_week_under_reasonable_time(ay):
    grade = Grade.objects.create(name="6А") if hasattr(Grade, "name") else Grade.objects.create(title="6А")
    subj  = Subject.objects.create(name="История") if hasattr(Subject, "name") else Subject.objects.create(title="История")
    lt    = LessonType.objects.create(key="lesson", label="Урок") if hasattr(LessonType, "key") else LessonType.objects.create(label="Урок")
    tw    = TemplateWeek.objects.create(is_active=True, academic_year=ay)

    User = apps.get_model("users", "User")
    teacher = User.objects.create(username="t_perf")

    for dow in (1,2,3,4,5):
        for i in range(4):
            TemplateLesson.objects.create(
                template_week=tw, day_of_week=dow, start_time=t(9 + i), duration_minutes=45,
                grade=grade, subject=subj, teacher=teacher, type=lt
            )

    d1, d2 = dt.date(2025, 9, 1), dt.date(2025, 9, 7)
    res = generate(d1, d2, debug=True)
    assert res.created == 20
    assert RealLesson.objects.count() == 20
