"""
Модуль core/serializers.py:
Сериализаторы моделей из справочников core (для REST API).
"""

from rest_framework import serializers
from .models import Grade, Subject, TeacherAvailability, WeeklyNorm, LessonType, AcademicYear
from .models import TeacherSubject, TeacherGrade, GradeSubject, StudentSubject


class TeacherAvailabilitySerializer(serializers.ModelSerializer):
    teacher = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = TeacherAvailability
        fields = ['id', 'teacher', 'day_of_week', 'start_time', 'end_time']

class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ['id', 'name']

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name']

class WeeklyNormSerializer(serializers.ModelSerializer):
    grade = GradeSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)
    class Meta:
        model = WeeklyNorm
        fields = ['id', 'grade', 'subject', 'hours_per_week', 'lessons_per_week', 'courses_per_week']

class LessonTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonType
        fields = ['id', 'key', 'label', 'counts_towards_norm']

class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = ['id', 'name']

class GradeSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeSubject
        fields = ['id', 'grade', 'subject']

class TeacherSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherSubject
        fields = ['id', 'teacher', 'subject']

class TeacherGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherGrade
        fields = ['id', 'teacher', 'grade']

class StudentSubjectSerializer(serializers.ModelSerializer):
    student = serializers.StringRelatedField()
    subject = serializers.StringRelatedField()
    grade = serializers.StringRelatedField()
    class Meta:
        model = StudentSubject
        fields = ['id', 'student', 'grade', 'subject']