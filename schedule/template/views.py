"""
Модуль template/views.py:
ViewSets для работы с шаблонными неделями и уроками.
"""

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from .models import TemplateWeek, TemplateLesson
from .serializers import TemplateWeekSerializer, TemplateLessonSerializer

from django.shortcuts import get_object_or_404

class TemplateWeekViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TemplateWeek.objects.all()
    serializer_class = TemplateWeekSerializer

    @action(detail=False, methods=["get"])
    def active_week(self, request):
        week = TemplateWeek.objects.filter(is_active=True).order_by('-created_at').first()
        if not week:
            return Response({"detail": "Нет активной недели"}, status=404)
        data = TemplateWeekSerializer(week).data
        return Response(data)

# Стандартный CRUD для уроков
class TemplateLessonViewSet(viewsets.ModelViewSet):
    queryset = TemplateLesson.objects.all()
    serializer_class = TemplateLessonSerializer


