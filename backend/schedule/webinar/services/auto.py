# backend/schedule/webinar/services/auto.py
from datetime import timedelta
from django.utils import timezone
from django.utils.text import slugify
from django.db.utils import ProgrammingError, OperationalError
from schedule.real_schedule.models import RealLesson, Room

def _ensure_room_for_lesson(lesson: RealLesson) -> Room:
    room = Room.objects.filter(type="LESSON", lesson_id=lesson.id).first()
    if room:
        return room
    start = lesson.start
    end = start + timedelta(minutes=lesson.duration_minutes or 0)
    jitsi_room = f"cedar-lesson-{lesson.id}"
    domain_default = Room._meta.get_field("jitsi_domain").default
    room = Room.objects.create(
        type="LESSON",
        lesson_id=lesson.id,
        jitsi_room=jitsi_room,
        jitsi_env="SELF_HOSTED",
        is_open=getattr(lesson, "is_open", False),
        status="SCHEDULED",
        scheduled_start=start,
        scheduled_end=end,
        join_url=f"https://{domain_default}/{jitsi_room}",
        auto_manage=True,
    )
    if not room.public_slug and room.is_open:
        room.public_slug = slugify(room.jitsi_room)
        room.save(update_fields=["public_slug"])
    return room

def _tables_ready() -> bool:
    try:
        # не кэшируем: спрашиваем у БД текущее состояние
        tables = set(connection.introspection.table_names())
        return (
            "real_schedule_reallesson" in tables and
            "real_schedule_room" in tables
        )
    except Exception:
        return False

def maintain_rooms() -> tuple[int, int]:
    """
    Создать комнаты за 15 минут до начала урока и закрыть через 10 минут после конца.
    Возвращает (created_count, closed_count).
    """
    if not _tables_ready():
        return 0, 0
    try:
        now = timezone.now()
        created = 0
        closed = 0

        # 1) создание комнат
        soon = now + timedelta(minutes=15)
        lessons = RealLesson.objects.filter(start__lte=soon, start__gte=now - timedelta(hours=6)).order_by("start")
        for lesson in lessons:
            existed = Room.objects.filter(type="LESSON", lesson_id=lesson.id).exists()
            room = _ensure_room_for_lesson(lesson)
            if not existed:
                created += 1
            # опционально переводим в OPEN в момент старта
            if room.status == "SCHEDULED" and lesson.start <= now <= (lesson.start + timedelta(minutes=1)):
                room.status = "OPEN"
                room.started_at = now
                room.save(update_fields=["status", "started_at"])

        # 2) закрытие «зависших»
        to_close = Room.objects.filter(
            type="LESSON",
            scheduled_end__lte=now - timedelta(minutes=10),
        ).exclude(status="CLOSED")
        for room in to_close:
            room.status = "CLOSED"
            if not room.ended_at:
                room.ended_at = now
            room.save(update_fields=["status", "ended_at"])
            closed += 1

        return created, closed

    except (ProgrammingError, OperationalError):
        # Таблиц ещё нет (миграции не применились) — тихо пропускаем цикл
        return 0, 0

def precreate_rooms_for_open_lessons(hours_ahead: int = 48) -> int:
    """Для открытых уроков (is_open=True) на горизонте H часов — заранее создать комнаты."""
    if not _tables_ready():
        return 0
    try:
        now = timezone.now()
        until = now + timedelta(hours=hours_ahead)
        cnt = 0
        qs = RealLesson.objects.filter(start__gte=now, start__lte=until, is_open=True)
        for lesson in qs:
            if not Room.objects.filter(type="LESSON", lesson_id=lesson.id).exists():
                _ensure_room_for_lesson(lesson)
                cnt += 1
        return cnt
    except (ProgrammingError, OperationalError):
        return 0
