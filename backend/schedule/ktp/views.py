"""
Модуль ktp/views.py:
View-функции для управления календарно-тематическими планами.
"""

from rest_framework import viewsets
from .models import KTPTemplate, KTPSection, KTPEntry
from .serializers import KTPTemplateSerializer, KTPSectionSerializer, KTPEntrySerializer

class KTPTemplateViewSet(viewsets.ModelViewSet):
    queryset = KTPTemplate.objects.all()
    serializer_class = KTPTemplateSerializer

class KTPSectionViewSet(viewsets.ModelViewSet):
    queryset = KTPSection.objects.all()
    serializer_class = KTPSectionSerializer

class KTPEntryViewSet(viewsets.ModelViewSet):
    queryset = KTPEntry.objects.all()
    serializer_class = KTPEntrySerializer
