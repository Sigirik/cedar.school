import logging
from django.utils import timezone
from django.db import transaction

from schedule.template.models import TemplateWeek
from schedule.template.serializers import TemplateLessonWriteSerializer  # ← ДОЛЖЕН БЫТЬ

logger = logging.getLogger("cedar.draft.commit")


def commit_draft_to_template(draft_obj):
    """
    Публикует активный черновик в TemplateWeek и создаёт TemplateLesson'ы через
    TemplateLessonWriteSerializer. Поле 'type' из черновика маппится в FK 'type'.
    """
    data = (getattr(draft_obj, "data", {}) or {})
    lessons = data.get("lessons", [])

    week = TemplateWeek.objects.create(name=f"Draft {timezone.now():%Y-%m-%d %H:%M}")

    create_template_lessons_from_draft(draft_obj, week)  # ← Оставляем ТОЛЬКО ЭТОТ путь

    logger.info("commit_draft: published week id=%s; lessons=%s", week.id, len(lessons))
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
