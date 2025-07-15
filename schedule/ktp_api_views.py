# ktp_api_views.py — ViewSet'ы для работы с КТП и справочниками

from rest_framework import viewsets
from .models import (
    KTPTemplate,
    KTPSection,
    KTPEntry,
    Subject,
    Grade,
    WeeklyNorm,
)
from .serializers import (
    KTPTemplateSerializer,
    KTPSectionSerializer,
    KTPEntrySerializer,
    SubjectSerializer,
    GradeSerializer,
    TeacherSerializer,
    WeeklyNormSerializer,
)
from django.contrib.auth import get_user_model

User = get_user_model()

# 🔧 Основные модели КТП

class KTPTemplateViewSet(viewsets.ModelViewSet):
    queryset = KTPTemplate.objects.all()
    serializer_class = KTPTemplateSerializer

class KTPSectionViewSet(viewsets.ModelViewSet):
    queryset = KTPSection.objects.all()
    serializer_class = KTPSectionSerializer

class KTPEntryViewSet(viewsets.ModelViewSet):
    queryset = KTPEntry.objects.all()
    serializer_class = KTPEntrySerializer


# 📚 Справочные данные

class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

class GradeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer

class TeacherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(role="TEACHER")
    serializer_class = TeacherSerializer

class WeeklyNormViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WeeklyNorm.objects.all().select_related("grade", "subject")
    serializer_class = WeeklyNormSerializer
