import datetime as dt
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import models
from django.apps import apps

from schedule.real_schedule.services.pipeline import generate
from schedule.template.models import TemplateWeek, TemplateLesson
from schedule.core.models import Grade, Subject, LessonType
from schedule.ktp.models import KTPTemplate, KTPSection, KTPEntry
from schedule.real_schedule.models import RealLesson

User = get_user_model()

def t(h, m=0):
    return dt.time(h, m)

def get_or_create_academic_year():
    """Сначала пытаемся взять существующий AY, иначе создаём новый."""
    AY = apps.get_model("core", "AcademicYear")

    # берем самый актуальный уже существующий
    qs = AY.objects.all()
    if hasattr(AY, "is_current"):
        qs = qs.order_by("-is_current", "-id")
    else:
        qs = qs.order_by("-id")
    existing = qs.first()
    if existing:
        return existing

    # если в тестовой БД его нет – создаём с автозаполнением полей
    fields = {f.name: f for f in AY._meta.get_fields() if f.concrete and not f.auto_created}
    kwargs = {}

    if "name" in fields: kwargs["name"] = "2025-2026"
    if "title" in fields and "name" not in kwargs: kwargs["title"] = "2025-2026"
    if "is_current" in fields: kwargs["is_current"] = True

    start = dt.date(2025, 9, 1)
    end   = dt.date(2026, 5, 31)
    for cand in ("start_date", "date_start", "from_date"):
        if cand in fields: kwargs[cand] = start
    for cand in ("end_date", "date_end", "to_date"):
        if cand in fields: kwargs[cand] = end

    for name, f in fields.items():
        if name in kwargs or getattr(f, "primary_key", False):
            continue
        default_provided = getattr(f, "default", models.NOT_PROVIDED) is not models.NOT_PROVIDED
        if getattr(f, "null", False) or default_provided:
            continue
        if isinstance(f, models.CharField):
            kwargs[name] = "AY"
        elif isinstance(f, models.BooleanField):
            kwargs[name] = True
        elif isinstance(f, models.IntegerField):
            kwargs[name] = 1
        elif isinstance(f, models.DateField):
            kwargs[name] = start

    return AY.objects.create(**kwargs)

def create_lesson_type(label="Урок"):
    LT = LessonType
    fields = {f.name: f for f in LT._meta.get_fields() if f.concrete and not f.auto_created}
    kwargs = {}
    if "key" in fields: kwargs["key"] = "LESSON"
    if "label" in fields: kwargs["label"] = label
    if "counts_towards_norm" in fields: kwargs["counts_towards_norm"] = True

    for name, f in fields.items():
        if name in kwargs or getattr(f, "primary_key", False):
            continue
        default_provided = getattr(f, "default", models.NOT_PROVIDED) is not models.NOT_PROVIDED
        if getattr(f, "null", False) or default_provided:
            continue
        if isinstance(f, models.CharField):
            kwargs[name] = label
        elif isinstance(f, models.BooleanField):
            kwargs[name] = False
        elif isinstance(f, models.IntegerField):
            kwargs[name] = 1
    return LT.objects.create(**kwargs)

class GeneratePipelineTests(TestCase):
    def setUp(self):
        # берём существующий год или создаём один (в тестовой БД обычно пусто)
        self.ay = get_or_create_academic_year()

        # Grade / Subject
        self.grade = Grade.objects.create(name="2А") if hasattr(Grade, "name") else Grade.objects.create(title="2А")
        subj_field = "name" if hasattr(Subject, "name") else "title"
        self.subj_math = Subject.objects.create(**{subj_field: "Математика"})

        self.lt = create_lesson_type("Урок")
        self.teacher = User.objects.create(username="teach1", email="t@t.t")

        # TemplateWeek с academic_year и is_active
        tw_kwargs = {"is_active": True, "academic_year": self.ay}
        if hasattr(TemplateWeek, "name"):
            tw_kwargs["name"] = "TW"
        elif hasattr(TemplateWeek, "title"):
            tw_kwargs["title"] = "TW"
        self.tw = TemplateWeek.objects.create(**tw_kwargs)

        # два урока (пн/вт)
        TemplateLesson.objects.create(
            template_week=self.tw, day_of_week=0,
            start_time=t(10, 0), duration_minutes=45,
            grade=self.grade, subject=self.subj_math, teacher=self.teacher, type=self.lt,
        )
        TemplateLesson.objects.create(
            template_week=self.tw, day_of_week=1,
            start_time=t(10, 0), duration_minutes=45,
            grade=self.grade, subject=self.subj_math, teacher=self.teacher, type=self.lt,
        )

    def test_generate_uses_active_week_and_creates_two_days(self):
        res = generate(dt.date(2025, 9, 1), dt.date(2025, 9, 7), debug=True)
        self.assertEqual(res.created, 2)
        self.assertEqual(RealLesson.objects.count(), 2)

    def test_ktp_unique_assignment_and_fallback(self):
        tpl_kwargs = {"grade": self.grade, "subject": self.subj_math, "academic_year": self.ay}
        if hasattr(KTPTemplate, "name"):
            tpl_kwargs["name"] = "КТП Математика 2А"
        elif hasattr(KTPTemplate, "title"):
            tpl_kwargs["title"] = "КТП Математика 2А"
        tpl = KTPTemplate.objects.create(**tpl_kwargs)

        sec_kwargs = {"ktp_template": tpl, "order": 1}
        if hasattr(KTPSection, "name"):
            sec_kwargs["name"] = "Раздел 1"
        elif hasattr(KTPSection, "title"):
            sec_kwargs["title"] = "Раздел 1"
        KTPSection.objects.create(**sec_kwargs)
        sec = KTPSection.objects.filter(ktp_template=tpl).order_by("order").first()

        e1 = KTPEntry.objects.create(section=sec, order=1, title="Тема 1")
        e2 = KTPEntry.objects.create(section=sec, order=2, title="Тема 2")

        res = generate(dt.date(2025, 9, 1), dt.date(2025, 9, 7), debug=True)
        self.assertEqual(res.created, 2)
        ids = list(RealLesson.objects.order_by("start").values_list("ktp_entry_id", flat=True))
        self.assertCountEqual(ids, [e1.id, e2.id])

        # третий урок → тем 2 → один с fallback-темой
        TemplateLesson.objects.create(
            template_week=self.tw, day_of_week=2,
            start_time=t(10, 0), duration_minutes=45,
            grade=self.grade, subject=self.subj_math, teacher=self.teacher, type=self.lt,
        )
        res = generate(dt.date(2025, 9, 1), dt.date(2025, 9, 7), debug=True)
        self.assertEqual(res.created, 3)
        with_ktp = RealLesson.objects.exclude(ktp_entry_id=None).count()
        self.assertEqual(with_ktp, 2)
        self.assertTrue(
            RealLesson.objects.filter(ktp_entry__isnull=True, topic_title="Тему задаст учитель на уроке").exists()
        )

    def test_generate_is_idempotent_across_runs(self):
        res1 = generate(dt.date(2025, 9, 1), dt.date(2025, 9, 7), debug=True)
        res2 = generate(dt.date(2025, 9, 1), dt.date(2025, 9, 7), debug=True)
        self.assertEqual(RealLesson.objects.count(), res2.created)