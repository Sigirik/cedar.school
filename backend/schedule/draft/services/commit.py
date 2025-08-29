# draft/services/commit.py (примерное место)
import logging
from schedule.core.services.lesson_type_lookup import get_lesson_type_or_400

logger = logging.getLogger("cedar.draft.commit")

def _normalize_type_id_or_400(draft_lesson) -> int:
    """
    draft_lesson: dict или модель черновика.
    Ожидается поле 'type' в исходных данных черновика (строка или dict).
    """
    raw = None
    if isinstance(draft_lesson, dict):
        raw = draft_lesson.get("type")
    else:
        raw = getattr(draft_lesson, "type", None)

    lt = get_lesson_type_or_400(raw)
    return lt.id

def commit_draft_to_template(draft_obj, *args, **kwargs):
    # ... ваша существующая транзакционная логика, итерация по lessons ...
    for d in lessons:  # d — dict из draft.data['lessons']
        # ... маппинг прочих полей ...
        lesson_type_id = _normalize_type_id_or_400(d)

        template_lesson = TemplateLesson(
            # ...
            lesson_type_id=lesson_type_id,
            # ...
        )
        template_lesson.save()
        logger.info("commit_draft: lesson mapped type → id=%s", lesson_type_id)

    # ...
