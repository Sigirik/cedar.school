import logging
from django.utils import timezone
from django.db import transaction

from schedule.template.models import TemplateLesson, TemplateWeek
from schedule.template.serializers import TemplateLessonWriteSerializer  # ← ДОЛЖЕН БЫТЬ
from schedule.core.services.lesson_type_lookup import get_lesson_type_or_400

logger = logging.getLogger("cedar.draft.commit")


def commit_draft_to_template(draft_obj):
    data = (getattr(draft_obj, "data", {}) or {})
    lessons = data.get("lessons", [])
    week = TemplateWeek.objects.create(name="Draft ...")

    with transaction.atomic():
        for d in lessons:
            lt = get_lesson_type_or_400(d.get("type"))  # ← вот он, маппинг
            ser = TemplateLessonWriteSerializer(data=d)
            ser.is_valid(raise_exception=True)

            # Охранник входа: поле type присутствует?
            if "type" not in ser.initial_data:
                raise ValueError("commit_draft: no 'type' in lesson data before save")

            obj = ser.save(template_week=week)

            # Охранник выхода: FK проставлен?
            if not getattr(obj, "type_id", None):
                raise ValueError("commit_draft: type_id is None after serializer.save()")
            TemplateLesson.objects.create(
                template_week=week,
                subject_id=d["subject"], grade_id=d["grade"], teacher_id=d["teacher"],
                day_of_week=d["day_of_week"], start_time=d["start_time"], duration_minutes=d["duration_minutes"],
                type=lt,  # ← FK в поле модели называется `type`
            )
    return week


def create_template_lessons_from_draft(draft_obj, week: TemplateWeek):
    """
    Берёт draft.data['lessons'] и создаёт TemplateLesson через write-сериализатор.
    """
    data = (getattr(draft_obj, "data", {}) or {})
    lessons = data.get("lessons", [])

    with transaction.atomic():
        for d in lessons:
            ser = TemplateLessonWriteSerializer(data=d)
            ser.is_valid(raise_exception=True)
            # поле в модели называется template_week
            ser.save(template_week=week)
