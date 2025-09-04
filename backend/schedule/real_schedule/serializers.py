from __future__ import annotations

import datetime as dt
from typing import Optional

from rest_framework import serializers

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
    end = serializers.SerializerMethodField()
    subject = _RefSerializer(read_only=True)
    grade = _RefSerializer(read_only=True)
    teacher = serializers.SerializerMethodField()
    lesson_type = _LessonTypeRefSerializer(read_only=True)
    room = serializers.SerializerMethodField()

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
            "room",
        )

    def get_end(self, obj: RealLesson) -> str:
        end_dt = obj.start + dt.timedelta(minutes=obj.duration_minutes or 0)
        return end_dt.isoformat().replace("+00:00", "Z")

    def get_teacher(self, obj: RealLesson) -> dict:
        t = obj.teacher
        fio = getattr(t, "short_fio", None) or getattr(t, "username", None) or str(t)
        return {"id": getattr(t, "id", None), "fio": fio}

    def get_room(self, obj: RealLesson) -> Optional[dict]:
        """
        Аккуратно берём комнату без предположений о related_name.
        Возвращаем только lite-набор полей, нужный фронту.
        """
        # Пытаемся через commonly used related_name
        room = getattr(obj, "room", None)
        if room is None:
            # fallback: первый Room по FK lesson
            try:
                room = Room.objects.filter(lesson=obj).first()
            except Exception:
                room = None

        if not room:
            return None

        return {
            "provider": getattr(room, "provider", None),
            "join_url": getattr(room, "join_url", None),
        }
