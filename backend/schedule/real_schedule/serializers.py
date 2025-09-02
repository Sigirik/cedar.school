from __future__ import annotations

import os
import datetime as dt
from typing import Optional
from django.conf import settings
from rest_framework import serializers

from schedule.real_schedule.models import RealLesson, Room

try:
    from zoneinfo import ZoneInfo  # py3.9+
except Exception:  # pragma: no cover
    ZoneInfo = None  # на современных образах не понадобится


# Школьная TZ: по умолчанию Europe/Amsterdam, можно переопределить
_SCHOOL_TZ_NAME = getattr(settings, "SCHOOL_TIME_ZONE", None) or os.getenv("SCHOOL_TZ", "Europe/Amsterdam")
_SCHOOL_TZ = ZoneInfo(_SCHOOL_TZ_NAME) if ZoneInfo else None


# ——— Сериализаторы, используемые другими эндпойнтами (оставляем как были) ———

class _RefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()

class _LessonTypeRefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    key = serializers.CharField()
    label = serializers.CharField()

class RealLessonSerializer(serializers.ModelSerializer):
    """ Полная версия для generate/conduct и пр. """
    end = serializers.SerializerMethodField()
    subject = _RefSerializer(read_only=True)
    grade = _RefSerializer(read_only=True)
    lesson_type = _LessonTypeRefSerializer(read_only=True)
    teacher = serializers.SerializerMethodField()

    class Meta:
        model = RealLesson
        fields = (
            "id",
            "subject",
            "grade",
            "teacher",
            "start",
            "duration_minutes",
            "end",
            "lesson_type",
            "topic_order",
            "topic_title",
        )

    def get_end(self, obj: RealLesson) -> str:
        end_dt = obj.start + dt.timedelta(minutes=obj.duration_minutes or 0)
        return end_dt.isoformat().replace("+00:00", "Z")

    def get_teacher(self, obj: RealLesson) -> dict:
        t = obj.teacher
        fio = getattr(t, "short_fio", None) or getattr(t, "username", None) or str(t)
        return {"id": getattr(t, "id", None), "fio": fio}


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ("id", "lesson", "provider", "join_url", "started_at", "ended_at")
        read_only_fields = ("started_at", "ended_at")


# ——— Компакт для /api/real_schedule/my/ ———
# Формат совместим с утилитой: date + start_time (в школьной TZ), PK и слаг type.

class MyRealLessonSerializer(serializers.ModelSerializer):
    """
    Компактный формат для реального расписания:
      - subject/grade/teacher → PK
      - type → slug LessonType.key
      - date (YYYY-MM-DD) и start_time (HH:MM:SS) → вычислены из start с учётом школьной TZ
      - поле 'start' больше не отдаём
    """
    subject = serializers.PrimaryKeyRelatedField(read_only=True)
    grade   = serializers.PrimaryKeyRelatedField(read_only=True)
    teacher = serializers.PrimaryKeyRelatedField(read_only=True)
    type    = serializers.SlugRelatedField(read_only=True, source="lesson_type", slug_field="key")

    date       = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()

    class Meta:
        model = RealLesson
        fields = (
            "id",
            "subject",
            "grade",
            "teacher",
            "date",              # ← новая дата встречи (YYYY-MM-DD)
            "start_time",        # ← локальное время начала (HH:MM:SS)
            "duration_minutes",
            "type",
        )

    def _to_school_tz(self, dt_utc: dt.datetime) -> dt.datetime:
        if _SCHOOL_TZ:
            return dt_utc.astimezone(_SCHOOL_TZ)
        return dt_utc  # fallback (UTC), если ZoneInfo внезапно недоступен

    def get_date(self, obj: RealLesson) -> str:
        local_dt = self._to_school_tz(obj.start)
        return local_dt.date().isoformat()  # YYYY-MM-DD

    def get_start_time(self, obj: RealLesson) -> str:
        local_dt = self._to_school_tz(obj.start)
        return local_dt.strftime("%H:%M:%S")
