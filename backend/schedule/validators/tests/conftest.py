import pytest
from django.utils import timezone
from zoneinfo import ZoneInfo

@pytest.fixture(autouse=True)
def activate_moscow_tz(settings):
    settings.TIME_ZONE = "Europe/Moscow"
    timezone.activate(ZoneInfo("Europe/Moscow"))
    yield
    timezone.deactivate()

def _norm_code(entry: dict) -> str:
    raw = (entry.get("code") or entry.get("type") or "").strip()
    up = raw.upper().replace("-", "_")
    msg = (entry.get("message") or "").lower()

    # Явные коды
    if "TEACHER" in up and "OVERLAP" in up:
        return "TEACHER_OVERLAP"
    if "GRADE" in up and "OVERLAP" in up:
        return "GRADE_OVERLAP"
    if "ROOM" in up and "OVERLAP" in up:
        return "ROOM_OVERLAP"
    if "ZERO" in up and "DURATION" in up:
        return "ZERO_DURATION"
    if up == "MISSING_FIELDS" or "не заполнены поля" in msg:
        return "MISSING_FIELDS"

    # Фоллбек по сообщению (у тебя: «Пересечение по teacher/grade/room ...»)
    if "пересечение" in msg:
        if "teacher" in msg:
            return "TEACHER_OVERLAP"
        if "grade" in msg:
            return "GRADE_OVERLAP"
        if "room" in msg:
            return "ROOM_OVERLAP"

    return up or "UNKNOWN"