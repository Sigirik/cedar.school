"""
Модуль template/serializers.py:
Сериализаторы шаблонных недель и уроков.
"""

from rest_framework import serializers
from .models import TemplateWeek, TemplateLesson, ActiveTemplateWeek
from schedule.core.serializers import GradeSerializer, SubjectSerializer
from users.serializers import UserSerializer

class TemplateLessonSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    grade = GradeSerializer(read_only=True)
    teacher = UserSerializer(read_only=True)

    class Meta:
        model = TemplateLesson
        fields = ['id', 'subject', 'grade', 'teacher', 'day_of_week', 'start_time', 'duration_minutes', 'type']

class TemplateWeekSerializer(serializers.ModelSerializer):
    lessons = TemplateLessonSerializer(many=True, read_only=True)

    class Meta:
        model = TemplateWeek
        fields = ['id', 'name', 'description', 'created_at', 'lessons']

class ActiveTemplateWeekSerializer(serializers.ModelSerializer):
    template = TemplateWeekSerializer(read_only=True)

    class Meta:
        model = ActiveTemplateWeek
        fields = ['id', 'template', 'activated_at']
