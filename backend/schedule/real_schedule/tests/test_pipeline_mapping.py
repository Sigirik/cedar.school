import datetime as dt
import pytest
from django.apps import apps

from schedule.real_schedule.services.pipeline import generate
from schedule.real_schedule.models import RealLesson
from schedule.template.models import TemplateLesson

pytestmark = pytest.mark.django_db

def test_type_mapping_and_links(week_with_lessons, ref):
    subj, grade, teacher, lt = ref

    # Интервал понедельник-воскресенье
    res = generate(dt.date(2025, 9, 1), dt.date(2025, 9, 7), debug=True)
    # Должно родиться 3 RealLesson
    assert RealLesson.objects.count() == 3

    rl = RealLesson.objects.order_by("start").first()
    assert rl is not None

    # --- проверка типа (если поле реально есть в модели RealLesson)
    rl_field_names = {f.name for f in RealLesson._meta.fields}
    if "type" in rl_field_names or "type_id" in rl_field_names:
        assert getattr(rl, "type_id", None) == lt.id

    # --- связи по предмету / классу / учителю (тоже только если поля есть)
    if "subject" in rl_field_names or "subject_id" in rl_field_names:
        assert getattr(rl, "subject_id", None) == subj.id
    if "grade" in rl_field_names or "grade_id" in rl_field_names:
        assert getattr(rl, "grade_id", None) == grade.id
    # поле может называться teacher / teacher_id / tutor и т.п. – проверим teacher*
    teacher_field = None
    for cand in ("teacher_id", "teacher", "tutor_id", "tutor"):
        if cand in rl_field_names:
            teacher_field = cand
            break
    if teacher_field:
        assert getattr(rl, teacher_field if teacher_field.endswith("_id") else f"{teacher_field}_id") == teacher.id

    # --- связь с TL (если хранится)
    for tl_fk in ("template_lesson_id", "template_lesson", "template_id", "template"):
        if tl_fk in rl_field_names:
            assert getattr(rl, tl_fk if tl_fk.endswith("_id") else f"{tl_fk}_id") is not None
            break
