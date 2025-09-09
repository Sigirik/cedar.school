# backend/schedule/webinar/views_rooms.py
import uuid
from datetime import timedelta, datetime
from zoneinfo import ZoneInfo
from django.utils import timezone
from django.utils.text import slugify
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response

from schedule.real_schedule.models import RealLesson, Room  # модель Room пока остаётся здесь
from schedule.real_schedule.serializers import RoomSerializer, RealLessonSerializer  # используем уже готовый сериализатор
from .services.join import build_join_payload

def _gen_room_name(prefix: str) -> str:
    return f"cedar-{prefix}-{uuid.uuid4().hex[:6]}"

def _window_status(scheduled_start, scheduled_end):
    """
    Возвращает ('SCHEDULED'|'OPEN'|'ENDED', available_from, available_until)
    """
    now = timezone.now()
    available_from = scheduled_start - timedelta(minutes=15)
    available_until = scheduled_end + timedelta(minutes=10)
    if now < available_from:
        return "SCHEDULED", available_from, available_until
    if now > available_until:
        return "ENDED", available_from, available_until
    return "OPEN", available_from, available_until


class RoomByLessonView(APIView):
    """
    GET /api/rooms/by-lesson/{lesson_id}/?force=1
    Возвращает комнату типа LESSON, создаёт автоматически:
      • если текущее время >= (start - 15мин), ИЛИ
      • если ?force=1 и пользователь staff (для MVP).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_id: int):
        lesson = get_object_or_404(RealLesson, id=lesson_id)

        # ВАЖНО: у RealLesson нет поля 'end' — считаем его от duration_minutes
        scheduled_start = lesson.start
        if not scheduled_start or lesson.duration_minutes is None:
            return Response({"detail": "Lesson has no start/duration_minutes"}, status=400)
        scheduled_end = scheduled_start + timedelta(minutes=lesson.duration_minutes)

        room = Room.objects.filter(type="LESSON", lesson_id=lesson_id).first()

        force = request.query_params.get("force") in ("1", "true", "yes", "on")
        status_val, available_from, available_until = _window_status(scheduled_start, scheduled_end)
        now = timezone.now()

        should_create = False
        if room is None:
            if force and request.user.is_staff:
                should_create = True
            elif now >= available_from:
                should_create = True

        if should_create:
            name = _gen_room_name(f"lesson-{lesson_id}")
            status_val, _, _ = _window_status(scheduled_start, scheduled_end)
            room = Room.objects.create(
                type="LESSON",
                lesson_id=lesson_id,
                jitsi_room=name,
                jitsi_env="SELF_HOSTED",  # по умолчанию
                is_open=getattr(lesson, "is_open", False),
                status=status_val,
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                join_url=f"https://{Room._meta.get_field('jitsi_domain').default}/{name}",
                auto_manage=True,
            )

        if room:
            # поддержим автоматическое обновление статуса при чтении
            new_status, _, _ = _window_status(room.scheduled_start, room.scheduled_end)
            if new_status != room.status:
                room.status = new_status
                room.save(update_fields=["status"])
            return Response(RoomSerializer(room).data, status=200)

        # Рано — окно ещё не открылось, и force не разрешён
        return Response({
            "detail": "Room not available yet",
            "lesson_id": lesson_id,
            "available_from": available_from,
            "available_until": available_until,
        }, status=200)


class RoomRetrieveView(APIView):
    """
    GET /api/rooms/{id}/ — отдать любую комнату по id (в т.ч. MEETING).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, room_id: int):
        room = get_object_or_404(Room, id=room_id)
        return Response(RoomSerializer(room).data, status=200)


class MeetingCreateView(APIView):
    """
    POST /api/rooms/meeting/
    body: { "title": "...", "scheduled_start": ISO, "scheduled_end": ISO, "is_open": true/false }
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        data = request.data or {}
        try:
            scheduled_start = datetime.fromisoformat(str(data.get("scheduled_start")).replace("Z", "+00:00"))
            if scheduled_start.tzinfo is None:
                scheduled_start = scheduled_start.replace(tzinfo=ZoneInfo("UTC"))

            scheduled_end = datetime.fromisoformat(str(data.get("scheduled_end")).replace("Z", "+00:00"))
            if scheduled_end.tzinfo is None:
                scheduled_end = scheduled_end.replace(tzinfo=ZoneInfo("UTC"))
        except Exception:
            return Response({"detail": "Invalid scheduled_start/scheduled_end"}, status=400)

        is_open = bool(data.get("is_open", False))

        name = _gen_room_name("meeting")
        status_val, _, _ = _window_status(scheduled_start, scheduled_end)
        room = Room.objects.create(
            type="MEETING",
            lesson=None,
            jitsi_room=name,
            jitsi_env="SELF_HOSTED",
            is_open=is_open,
            status=status_val,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            join_url=f"https://{Room._meta.get_field('jitsi_domain').default}/{name}",
            auto_manage=True,
        )
        if room.is_open and not room.public_slug:
            room.public_slug = slugify(room.jitsi_room)
            room.save(update_fields=["public_slug"])
        return Response(RoomSerializer(room).data, status=201)

class RoomJoinView(APIView):
    """
    POST /api/rooms/{id}/join/  (auth required)
    body: {}
    returns: { join_url, you_are }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, room_id: int):
        room = get_object_or_404(Room, id=room_id)
        # enforce_closed_access=True → build_join_payload вернёт {"error":"forbidden"} для «посторонних»
        payload = build_join_payload(room, user=request.user, enforce_closed_access=True)
        if payload.get("error") == "forbidden":
            return Response({"detail": "Join is not allowed"}, status=403)
        return Response(payload, status=200)

class PublicRoomJoinView(APIView):
    """
    POST /api/public/rooms/{slug}/join/  (anonymous allowed)
    body: { display_name }
    """
    permission_classes = [AllowAny]

    def post(self, request, slug: str):
        room = get_object_or_404(Room, public_slug=slug, is_open=True)
        display_name = (request.data or {}).get("display_name") or "Гость"
        payload = build_join_payload(room, user=getattr(request, "user", None), display_name=display_name)
        # аноним всегда observer (функция сама так вернёт)
        return Response(payload, status=200)

class RoomCloseView(APIView):
    """
    POST /api/rooms/{id}/close/
    """
    permission_classes = [IsAdminUser]

    def post(self, request, room_id: int):
        room = get_object_or_404(Room, id=room_id)
        room.status = "CLOSED"
        room.ended_at = timezone.now()
        room.save(update_fields=["status", "ended_at"])
        return Response(RoomSerializer(room).data, status=200)


class RecordingMetaView(APIView):
    """
    GET /api/rooms/{id}/recording/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, room_id: int):
        room = get_object_or_404(Room, id=room_id)
        return Response({
            "status": room.recording_status,
            "file_url": room.recording_file_url,
            "started_at": room.recording_started_at,
            "ended_at": room.recording_ended_at,
            "duration_secs": room.recording_duration_secs,
        }, status=200)

class OpenLessonsFeedView(APIView):
    """
    GET /api/rooms/open-lessons/
      Параметры:
        - all=1                → игнорировать окно времени (всё)
        - since_hours=<int>    → сколько часов назад брать (по умолчанию 0.1667 ≈ 10 минут)
        - hours=<int>          → сколько часов вперёд (по умолчанию 48)
    Логика:
      1) Берём RealLesson.is_open=True в окне времени.
         Если нет Room — создаём SCHEDULED с public_slug.
      2) Плюсом добавляем уже существующие Room(type='LESSON', is_open=True) в этом же окне.
         (Чтобы показать открытые комнаты, даже если урок не помечен is_open.)
      3) Дедуп по lesson_id/room_id.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()

        all_flag = str(request.GET.get("all", "")).lower() in ("1","true","yes","on")
        try:
            since_hours = float(request.GET.get("since_hours", "0.1667"))  # ~10 минут назад
        except Exception:
            since_hours = 0.1667
        try:
            hours = float(request.GET.get("hours", "48"))
        except Exception:
            hours = 48.0

        if all_flag:
            since = now - timedelta(days=3650)
            until = now + timedelta(days=3650)
        else:
            since = now - timedelta(hours=since_hours)
            until = now + timedelta(hours=hours)

        items = []
        seen_room_ids = set()
        seen_lesson_ids = set()

        # 1) Уроки is_open=True
        lessons = (RealLesson.objects
                   .select_related("subject","grade","teacher")
                   .filter(is_open=True, start__gte=since, start__lte=until)
                   .order_by("start"))

        for lesson in lessons:
            seen_lesson_ids.add(lesson.id)
            room = Room.objects.filter(type="LESSON", lesson_id=lesson.id).first()
            if not room:
                start = lesson.start
                end = start + timedelta(minutes=lesson.duration_minutes or 0)
                jitsi_room = f"cedar-lesson-{lesson.id}"
                domain_default = Room._meta.get_field("jitsi_domain").default
                room = Room.objects.create(
                    type="LESSON",
                    lesson_id=lesson.id,
                    jitsi_room=jitsi_room,
                    jitsi_env="SELF_HOSTED",
                    is_open=True,
                    status="SCHEDULED",
                    scheduled_start=start,
                    scheduled_end=end,
                    join_url=f"https://{domain_default}/{jitsi_room}",
                    auto_manage=True,
                )
                if not room.public_slug:
                    room.public_slug = slugify(room.jitsi_room)
                    room.save(update_fields=["public_slug"])

            items.append({
                "room_id": room.id,
                "public_slug": room.public_slug,
                "status": room.status,
                "scheduled_start": room.scheduled_start,
                "scheduled_end": room.scheduled_end,
                "lesson": RealLessonSerializer(lesson).data,
            })
            seen_room_ids.add(room.id)

        # 2) Фолбэк: открытые комнаты в том же окне (могут быть без is_open у урока)
        rooms = (Room.objects
                 .select_related("lesson","lesson__subject","lesson__grade","lesson__teacher")
                 .filter(type="LESSON", is_open=True,
                         scheduled_start__lte=until, scheduled_end__gte=since)
                 .order_by("scheduled_start"))

        for r in rooms:
            if r.id in seen_room_ids:
                continue
            lesson = r.lesson
            # Если есть lesson и он уже добавлен как открытый — пропустим
            if lesson and lesson.id in seen_lesson_ids:
                continue
            items.append({
                "room_id": r.id,
                "public_slug": r.public_slug,
                "status": r.status,
                "scheduled_start": r.scheduled_start,
                "scheduled_end": r.scheduled_end,
                "lesson": RealLessonSerializer(lesson).data if lesson else None,
            })
            seen_room_ids.add(r.id)

        return Response(items, status=200)