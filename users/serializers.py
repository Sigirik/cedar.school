from rest_framework import serializers
from users.models import User
from schedule.core.models import TeacherSubject, TeacherGrade, StudentSubject, GradeSubject
from schedule.core.serializers import (
    TeacherSubjectSerializer, TeacherGradeSerializer,
    StudentSubjectSerializer, GradeSubjectSerializer
)

class UserSerializer(serializers.ModelSerializer):
    middle_name = serializers.CharField(read_only=True)
    subjects = serializers.SerializerMethodField()
    grades = serializers.SerializerMethodField()
    individual_subjects_enabled = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'last_name', 'first_name', 'middle_name', 'role',
            'subjects', 'grades', 'individual_subjects_enabled'
        ]

    def get_subjects(self, obj):
        if obj.role == User.Role.STUDENT and getattr(obj, 'individual_subjects_enabled', False):
            # Индивидуальные предметы через StudentSubject
            qs = StudentSubject.objects.filter(student=obj)
            return StudentSubjectSerializer(qs, many=True).data
        elif obj.role == User.Role.STUDENT:
            # Предметы класса через GradeSubject (требуется связь user → grade!)
            # !!! Требуется реализовать obj.grade !!!
            if hasattr(obj, 'grade'):
                qs = GradeSubject.objects.filter(grade=obj.grade)
                return GradeSubjectSerializer(qs, many=True).data
            return []
        else:
            qs = TeacherSubject.objects.filter(teacher=obj)
            return TeacherSubjectSerializer(qs, many=True).data

    def get_grades(self, obj):
        if obj.role == User.Role.TEACHER:
            qs = TeacherGrade.objects.filter(teacher=obj)
            return TeacherGradeSerializer(qs, many=True).data
        return []