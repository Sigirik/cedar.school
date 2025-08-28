# schedule/real_schedule/views.py
from collections import Counter
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
from schedule.real_schedule.services.pipeline import generate, CollisionError



def _parse_date_value(value):
    if value is None: return None
    if isinstance(value, dt.date): return value
    if isinstance(value, str) and value.strip():
        try: return parse_date(value)
        except Exception: return None
    return None

def _parse_range(request):
    raw_from = request.data.get("from") or request.query_params.get("from")
    raw_to   = request.data.get("to")   or request.query_params.get("to")
    d_from = _parse_date_value(raw_from)
    d_to   = _parse_date_value(raw_to)
    if not d_from or not d_to or d_from > d_to:
        return None, None
    return d_from, d_to

def _parse_bool(v):
    if isinstance(v, bool): return v
    if isinstance(v, int):  return v != 0
    if isinstance(v, str):  return v.strip().lower() in ("1","true","yes","on")
    return False

# ...
    raw_debug = request.data.get("debug") or request.query_params.get("debug")
    debug_flag = _parse_bool(raw_debug)

    res = generate(from_date, to_date, debug=debug_flag)

    warnings = res.warnings or []
# сгруппируем по паре "grade/subject" из твоего текста
def _key(w):
    try:
        return w["message"].split()[-1]   # последний токен вида "G/S"
    except Exception:
        return "unknown"

    warnings_summary = dict(Counter(map(_key, warnings)))

    return Response({
        "version": res.version,
        "generation_batch_id": res.generation_batch_id,
        "deleted": res.deleted,
        "created": res.created,
        "warnings": warnings,
        "warnings_count": len(warnings),
        "warnings_summary": warnings_summary,
    })

def _warn_key(w):
    # "Нет KTPEntry для 2025-09-01 2/3" → "2/3"
    try: return w["message"].split()[-1]
    except Exception: return "unknown"

class GenerateRealScheduleView(APIView):
    # permission_classes = [IsAdminUser]

    def post(self, request):
        d_from, d_to = _parse_range(request)
        if not d_from:
            return Response({"detail": "INVALID_RANGE"}, status=400)

        tpl_id_raw = request.data.get("template_week_id") or request.query_params.get("template_week_id")
        tpl_id = int(tpl_id_raw) if tpl_id_raw not in (None, "",) else None

        raw_rewrite = request.data.get("rewrite_from") or request.query_params.get("rewrite_from")
        rewrite_from = _parse_date_value(raw_rewrite) or d_from

        raw_debug = request.data.get("debug") or request.query_params.get("debug")
        debug_flag = _parse_bool(raw_debug)

        try:
            res = generate(
                from_date=d_from,
                to_date=d_to,
                template_week_id=tpl_id,
                rewrite_from=rewrite_from,
                debug=debug_flag,
            )
        except CollisionError as e:
            return Response({
                "detail": "COLLISIONS",
                **(e.details or {}),
            }, status=400)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)
        except Exception as e:
            return Response({"detail": "INTERNAL_ERROR", "error": str(e)}, status=500)

        warnings = res.warnings or []
        warnings_count   = len(warnings)
        warnings_summary = dict(Counter(map(_warn_key, warnings)))

        # Сколько создано с темой/без темы в ЭТОМ запуске
        created_total       = res.created
        created_without_ktp = warnings_count
        created_with_ktp    = created_total - created_without_ktp

        return Response({
            "version": res.version,
            "generation_batch_id": res.generation_batch_id,
            "deleted": res.deleted,
            "created": created_total,
            "created_with_ktp": created_with_ktp,
            "created_without_ktp": created_without_ktp,
            "warnings_count": warnings_count,
            "warnings_summary": warnings_summary,
            "warnings": warnings,
        }, status=201)


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
