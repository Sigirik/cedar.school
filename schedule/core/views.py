"""
Модуль core/views.py:
ViewSet'ы для CRUD-операций справочников core через REST API.
"""

from rest_framework import viewsets
from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import Grade, Subject, TeacherAvailability, WeeklyNorm, LessonType, AcademicYear, GradeSubject, StudentSubject
from .serializers import GradeSerializer, SubjectSerializer, TeacherAvailabilitySerializer, WeeklyNormSerializer, LessonTypeSerializer, AcademicYearSerializer, GradeSubjectSerializer, StudentSubjectSerializer


class GradeViewSet(ReadOnlyModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer

class SubjectViewSet(ReadOnlyModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

class TeacherAvailabilityViewSet(ReadOnlyModelViewSet):
    queryset = TeacherAvailability.objects.select_related('teacher').all()
    serializer_class = TeacherAvailabilitySerializer

class WeeklyNormViewSet(ReadOnlyModelViewSet):
    queryset = WeeklyNorm.objects.select_related('grade', 'subject').all()
    serializer_class = WeeklyNormSerializer

class LessonTypeViewSet(ReadOnlyModelViewSet):
    queryset = LessonType.objects.all()
    serializer_class = LessonTypeSerializer

class AcademicYearViewSet(ReadOnlyModelViewSet):
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer

class GradeSubjectViewSet(viewsets.ModelViewSet):
    queryset = GradeSubject.objects.select_related('grade', 'subject').all()
    serializer_class = GradeSubjectSerializer

class StudentSubjectViewSet(viewsets.ModelViewSet):
    queryset = StudentSubject.objects.select_related('student', 'grade', 'subject').all()
    serializer_class = StudentSubjectSerializer