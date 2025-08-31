from typing import Any, Dict, Optional, Union
from rest_framework.exceptions import ValidationError
from schedule.core.models import LessonType

Payload = Union[str, Dict[str, Any]]

def _strip_or_none(v: Optional[str]) -> Optional[str]:
    return v.strip() if isinstance(v, str) else None

def get_lesson_type_or_400(payload: Payload) -> LessonType:
    """
    Поддерживает:
      - "lecture"  (строка по key/label, регистр не важен)
      - {"key": "..."} / {"label": "..."}
    """
    if payload is None or (isinstance(payload, dict) and not payload):
        raise ValidationError({"type": "Тип урока обязателен (key или label)."})

    key = label = None
    if isinstance(payload, dict):
        key = _strip_or_none(payload.get("key"))
        label = _strip_or_none(payload.get("label"))
    else:
        s = _strip_or_none(str(payload))
        key = label = s

    qs = LessonType.objects.all()
    lt = qs.filter(key__iexact=key).first() if key else None
    if lt is None and label:
        lt = qs.filter(label__iexact=label).first()
    if lt:
        return lt

    available = list(qs.values("key", "label"))
    raise ValidationError({
        "type": {
            "message": "Неизвестный тип урока. Используйте 'key' или 'label'.",
            "received": payload,
            "available": available,
            "hint": "Напр.: {'type': {'key': 'lecture'}} или {'type': {'label': 'Лекция'}}",
        }
    })
