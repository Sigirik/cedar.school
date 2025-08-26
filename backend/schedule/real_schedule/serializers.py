from rest_framework import serializers
from .models import RealLesson
from schedule.core.serializers import SubjectSerializer, GradeSerializer, UserSerializer
from schedule.template.serializers import TemplateLessonSerializer

class RealLessonSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    grade = GradeSerializer(read_only=True)
    teacher = UserSerializer(read_only=True)
    template_lesson = TemplateLessonSerializer(read_only=True)

    class Meta:
        model = RealLesson
        fields = [
            'id', 'date', 'day_of_week', 'subject', 'grade', 'teacher',
            'start_time', 'duration_minutes', 'topic', 'theme_from_ktp', 'template_lesson'
        ]
