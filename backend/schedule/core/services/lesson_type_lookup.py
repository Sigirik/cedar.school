from typing import Any, Dict, Optional, Union
from django.db.models import Q
from rest_framework.exceptions import ValidationError
from schedule.core.models import LessonType

Payload = Union[str, Dict[str, Any]]

def _strip_or_none(v: Optional[str]) -> Optional[str]:
    return v.strip() if isinstance(v, str) else None

def get_lesson_type_or_400(payload: Payload) -> LessonType:
    """
    Принимает:
      - строку -> пробуем как key, затем как label (case-insensitive)
      - dict -> пробуем {'key': ...} и/или {'label': ...}
    Возвращает LessonType или бросает DRF ValidationError 400 с подсказками.
    """
    if payload is None or (isinstance(payload, dict) and not payload):
        raise ValidationError({"type": "Тип урока обязателен (key или label)."})

    key = label = None
    if isinstance(payload, dict):
        key = _strip_or_none(payload.get("key"))
        label = _strip_or_none(payload.get("label"))
    else:
        # payload — строка: пытаемся и как key, и как label
        s = _strip_or_none(str(payload))
        key, label = s, s

    qs = LessonType.objects.all()
    lt = None

    if key:
        lt = qs.filter(key__iexact=key).first()
    if lt is None and label:
        lt = qs.filter(label__iexact=label).first()

    if lt is not None:
        return lt

    available = list(qs.values("key", "label"))
    raise ValidationError({
        "type": {
            "message": "Неизвестный тип урока. Используйте 'key' или 'label'.",
            "received": payload,
            "available": available,
            "hint": "Например: {'type': {'key': 'lecture'}} или {'type': {'label': 'Лекция'}}"
        }
    })
