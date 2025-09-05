from __future__ import annotations

import datetime as dt
from typing import Optional
from django.utils import timezone
from django.utils.timezone import localtime, is_aware
from rest_framework import serializers
from zoneinfo import ZoneInfo

from schedule.real_schedule.models import RealLesson, Room


# ——— Вспомогательные мини-сериализаторы ———

class _RefSerializer(serializers.Serializer):
    """Унифицированный вид для справочников: {id, name}"""
    id = serializers.IntegerField()
    name = serializers.CharField()


class _TeacherRefSerializer(serializers.Serializer):
    """Учитель: {id, fio} (короткое ФИО или username)"""
    id = serializers.IntegerField()
    fio = serializers.CharField()


class _LessonTypeRefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    key = serializers.CharField()
    label = serializers.CharField()

def _local_dt(dt):
    if dt is None:
        return None
    try:
        return localtime(dt) if is_aware(dt) else dt
    except Exception:
        # на всякий случай не падаем из-за неправильных tz
        return dt
# ——— Основные сериализаторы, используемые за пределами /my/ ———

class RealLessonSerializer(serializers.ModelSerializer):
    """
    Полный сериализатор RealLesson для уже существующих эндпойнтов (generate, conduct, и т.п.)
    Сохранил состав полей максимально консервативным.
    """
    end = serializers.SerializerMethodField()
    # ВАЖНО: не указываем source='subject'|'grade'|'lesson_type' — это ломает DRF 3.16+
    subject = _RefSerializer(read_only=True)
    grade = _RefSerializer(read_only=True)
    teacher = serializers.SerializerMethodField()
    lesson_type = _LessonTypeRefSerializer(read_only=True)

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
            # Ниже поля оставлены только те, что точно существуют в модели.
            # Если в твоей модели есть дополнительные (ktp_entry и пр.) — можно добавить здесь.
        )

    def get_end(self, obj: RealLesson) -> str:
        end_dt = obj.start + dt.timedelta(minutes=obj.duration_minutes or 0)
        # единый ISO8601 с Z для UTC
        return end_dt.isoformat().replace("+00:00", "Z")

    def get_teacher(self, obj: RealLesson) -> dict:
        t = obj.teacher
        # поддержка короткого ФИО, если есть
        fio = getattr(t, "short_fio", None) or getattr(t, "username", None) or str(t)
        return {"id": getattr(t, "id", None), "fio": fio}


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ("id", "lesson", "provider", "join_url", "started_at", "ended_at")
        read_only_fields = ("started_at", "ended_at")


# ——— Компактный сериализатор для /api/real_schedule/my/ ———

class MyRealLessonSerializer(serializers.ModelSerializer):
    subject = serializers.IntegerField(source="subject_id")
    grade = serializers.IntegerField(source="grade_id")
    teacher = serializers.IntegerField(source="teacher_id")

    # было: type = _LessonTypeRefSerializer(read_only=True)
    # стало: ключ типа (str), берём из lesson_type.key
    type = serializers.SerializerMethodField()

    date = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()

    class Meta:
        model = RealLesson
        fields = (
            "id",
            "subject",
            "grade",
            "teacher",
            "date",
            "start_time",
            "duration_minutes",
            "type",
            "room",
        )

    def _get_target_tz(self) -> ZoneInfo:
        # Можно будет расширить: взять user.profile.timezone или заголовок X-TZ
        tz_name = (self.context or {}).get("tz") or "Europe/Amsterdam"
        try:
            return ZoneInfo(tz_name)
        except Exception:
            return ZoneInfo("Europe/Amsterdam")

    def get_date(self, obj):
        dt = obj.start
        if dt is None:
            return None
        if is_aware(dt):
            dt = dt.astimezone(self._get_target_tz())
        return dt.date().isoformat()

    def get_start_time(self, obj):
        dt = obj.start
        if dt is None:
            return None
        if is_aware(dt):
            dt = dt.astimezone(self._get_target_tz())
        return dt.time().isoformat()

    def get_type(self, obj):
        lt = getattr(obj, "lesson_type", None)
        return getattr(lt, "key", None) if lt else None

    def get_room(self, obj):
        r = getattr(obj, "room", None)
        if not r:
            return None
        return {"provider": getattr(r, "provider", None), "join_url": getattr(r, "join_url", None)}