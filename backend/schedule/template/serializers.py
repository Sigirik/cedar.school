"""
Модуль template/serializers.py:
Сериализаторы шаблонных недель и уроков.
"""

from rest_framework import serializers
from .models import TemplateWeek, TemplateLesson, ActiveTemplateWeek
from schedule.core.serializers import GradeSerializer, SubjectSerializer
from users.serializers import UserSerializer

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
