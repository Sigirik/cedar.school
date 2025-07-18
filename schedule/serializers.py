from rest_framework import serializers, viewsets
from .models import KTPTemplate, KTPSection, KTPEntry, TemplateWeekDraft, TemplateWeek, TemplateLesson, WeeklyNorm
from schedule.models import TeacherAvailability

class KTPEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = KTPEntry
        fields = '__all__'

class KTPSectionSerializer(serializers.ModelSerializer):
    entries = KTPEntrySerializer(many=True, read_only=True)

    class Meta:
        model = KTPSection
        fields = '__all__'

class KTPTemplateSerializer(serializers.ModelSerializer):
    sections = KTPSectionSerializer(many=True, read_only=True)

    class Meta:
        model = KTPTemplate
        fields = '__all__'

class TemplateWeekDraftSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TemplateWeekDraft
        fields = "__all__"

class TemplateLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateLesson
        fields = ["id", "subject", "grade", "teacher", "day_of_week", "start_time", "duration_minutes", "type"]

class TemplateWeekDetailSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField()

    class Meta:
        model = TemplateWeek
        fields = ["id", "name", "academic_year", "created_at", "is_active", "lessons"]

    def get_lessons(self, obj):
        lessons = TemplateLesson.objects.filter(template_week=obj)
        return TemplateLessonSerializer(lessons, many=True).data

class TemplateWeekSerializer(serializers.ModelSerializer):
    lessons = TemplateLessonSerializer(many=True, read_only=True)

    class Meta:
        model = TemplateWeek
        fields = ['id', 'name', 'academic_year', 'created_at', 'is_active', 'lessons']

from .models import Subject, Grade
from django.contrib.auth import get_user_model

User = get_user_model()

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name"]

class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ["id", "name"]

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name"]

class WeeklyNormSerializer(serializers.ModelSerializer):
    grade_name = serializers.CharField(source="grade.name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)

    class Meta:
        model = WeeklyNorm
        fields = [
            "id",
            "grade", "grade_name",
            "subject", "subject_name",
            "hours_per_week",
            "lessons_per_week",
            "courses_per_week"
        ]

class TeacherAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherAvailability
        fields = ['id', 'teacher', 'day_of_week', 'start_time', 'end_time']


