"""
Модуль template/serializers.py:
Сериализаторы шаблонных недель и уроков.
"""

from rest_framework import serializers
from .models import TemplateWeek, TemplateLesson, ActiveTemplateWeek
from schedule.core.services.lesson_type_lookup import get_lesson_type_or_400
from schedule.core.models import Subject, Grade
from users.models import User

class TemplateLessonSerializer(serializers.ModelSerializer):
    subject = serializers.PrimaryKeyRelatedField(read_only=True)
    grade = serializers.PrimaryKeyRelatedField(read_only=True)
    teacher = serializers.PrimaryKeyRelatedField(read_only=True)
    type = serializers.SlugRelatedField(read_only=True, slug_field='key')

    class Meta:
        model = TemplateLesson
        fields = [
            "id",
            "subject",
            "grade",
            "teacher",
            "day_of_week",
            "start_time",
            "duration_minutes",
            "type"
        ]

class TemplateWeekSerializer(serializers.ModelSerializer):
    lessons = TemplateLessonSerializer(many=True, read_only=True)

    class Meta:
        model = TemplateWeek
        fields = [
            "id",
            "name",
            "created_at",
            "lessons",
        ]

class ActiveTemplateWeekSerializer(serializers.ModelSerializer):
    template = TemplateWeekSerializer(read_only=True)

    class Meta:
        model = ActiveTemplateWeek
        fields = ['id', 'template', 'activated_at']

class TemplateLessonWriteSerializer(serializers.ModelSerializer):
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    grade   = serializers.PrimaryKeyRelatedField(queryset=Grade.objects.all())
    teacher = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    type    = serializers.JSONField(write_only=True)

    class Meta:
        model = TemplateLesson
        fields = [
            "subject", "grade", "teacher",
            "day_of_week", "start_time", "duration_minutes",
            "type",
        ]

    def validate_type(self, value):
        self._lt = get_lesson_type_or_400(value)
        return value

    def create(self, validated_data):
        validated_data.pop("type", None)
        validated_data["type"] = getattr(self, "_lt", None)  # FK → поле модели `type`
        return super().create(validated_data)