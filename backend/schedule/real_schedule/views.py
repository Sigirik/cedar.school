import datetime as dt
from datetime import timezone as dt_timezone
from django.utils.dateparse import parse_date
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAdminUser  # TODO: директор/завуч/учитель
from rest_framework.response import Response
from rest_framework.views import APIView

from schedule.real_schedule.models import RealLesson, Room
from schedule.real_schedule.serializers import RealLessonSerializer, RoomSerializer
from schedule.real_schedule.services.pipeline import generate


def _parse_date_value(value):
    """Аккуратно разбираем дату из JSON/Query: str|date|None -> date|None"""
    if value is None:
        return None
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return parse_date(value)
        except Exception:
            return None
    return None

def _parse_range(request):
    # поддержим и JSON, и query (?from=&to=)
    raw_from = request.data.get("from") or request.query_params.get("from")
    raw_to   = request.data.get("to")   or request.query_params.get("to")
    d_from = _parse_date_value(raw_from)
    d_to   = _parse_date_value(raw_to)
    if not d_from or not d_to or d_from > d_to:
        return None, None
    return d_from, d_to


class GenerateRealScheduleView(APIView):
    # permission_classes = [IsAdminUser]  # как у тебя сейчас

    def post(self, request):
        d_from, d_to = _parse_range(request)
        if not d_from:
            return Response({"detail": "INVALID_RANGE"}, status=400)

        raw_rewrite = request.data.get("rewrite_from") or request.query_params.get("rewrite_from")
        rewrite_from = _parse_date_value(raw_rewrite) or d_from

        tpl_id = request.data.get("template_week_id") or request.query_params.get("template_week_id")

        try:
            res = generate(from_date=d_from, to_date=d_to, template_week_id=tpl_id, rewrite_from=rewrite_from)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)
        except Exception as e:
            # на время отладки можно оставить, потом убрать
            return Response({"detail": "INTERNAL_ERROR", "error": str(e)}, status=500)

        return Response({
            "version": res.version,
            "generation_batch_id": res.generation_batch_id,
            "deleted": res.deleted,
            "created": res.created,
            "warnings": res.warnings
        }, status=status.HTTP_201_CREATED)


class ConductLessonView(APIView):
    permission_classes = [IsAdminUser]  # TODO: teacher of lesson OR director

    def post(self, request, pk: int):
        try:
            lesson = RealLesson.objects.select_related("ktp_entry").get(pk=pk)
        except RealLesson.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        ts = request.data.get("conducted_at")
        if ts:
            # поддержим формат "...Z"
            val = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
            dt_ts = timezone.make_aware(val, dt_timezone.utc) if val.tzinfo is None else val
        else:
            dt_ts = timezone.now()

        if not lesson.conducted_at:
            lesson.conducted_at = dt_ts
            lesson.save(update_fields=["conducted_at", "updated_at"])
            if lesson.ktp_entry_id:
                from schedule.ktp.models import KTPEntry
                KTPEntry.objects.filter(id=lesson.ktp_entry_id, actual_date__isnull=True)\
                                .update(actual_date=dt_ts.date())

        return Response(RealLessonSerializer(lesson).data, status=200)


class RoomGetOrCreateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        lesson_id = request.data.get("lesson_id")
        provider  = request.data.get("provider", "JITSI")
        join_url  = request.data.get("join_url")
        if not (lesson_id and join_url):
            return Response({"detail": "lesson_id and join_url required"}, status=400)

        room, created = Room.objects.get_or_create(
            lesson_id=lesson_id,
            defaults={"provider": provider, "join_url": join_url}
        )
        return Response(RoomSerializer(room).data, status=201 if created else 200)


class RoomEndView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk: int):
        try:
            room = Room.objects.select_related("lesson").get(pk=pk)
        except Room.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)
        room.ended_at = timezone.now()
        room.save(update_fields=["ended_at"])
        return Response(RoomSerializer(room).data, status=200)
