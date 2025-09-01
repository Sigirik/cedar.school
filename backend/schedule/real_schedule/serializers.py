from __future__ import annotations

import datetime as dt
from typing import Optional
from rest_framework import serializers

from schedule.real_schedule.models import RealLesson, Room


# ——— Используется другими эндпойнтами (оставляем как было) ———

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


# ——— Компактная версия для /api/real_schedule/my/ ———

class MyRealLessonSerializer(serializers.ModelSerializer):
    """
    Компактный формат в стиле шаблона:
      - subject/grade/teacher → PK
      - type → slug LessonType.key
    """
    subject = serializers.PrimaryKeyRelatedField(read_only=True)
    grade   = serializers.PrimaryKeyRelatedField(read_only=True)
    teacher = serializers.PrimaryKeyRelatedField(read_only=True)
    type    = serializers.SlugRelatedField(read_only=True, source="lesson_type", slug_field="key")

    class Meta:
        model = RealLesson
        fields = (
            "id",
            "subject",
            "grade",
            "teacher",
            "start",
            "duration_minutes",
            "type",
        )
