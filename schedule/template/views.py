"""
Модуль template/views.py:
ViewSets для работы с шаблонными неделями и уроками.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import TemplateWeek, ActiveTemplateWeek, TemplateLesson
from .serializers import TemplateWeekSerializer, TemplateLessonSerializer, ActiveTemplateWeekSerializer

class TemplateWeekViewSet(viewsets.ModelViewSet):
    queryset = TemplateWeek.objects.all()
    serializer_class = TemplateWeekSerializer

    @action(detail=False, methods=['get'])
    def active(self, request):
        active_week = ActiveTemplateWeek.objects.select_related('template').first()
        if not active_week:
            return Response({"detail": "Нет активной недели"}, status=404)
        serializer = ActiveTemplateWeekSerializer(active_week)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def lessons(self, request, pk=None):
        # Вернуть сериализованные уроки для недели — в расширенном формате
        template_week = self.get_object()
        lessons = TemplateLesson.objects.filter(template_week=template_week).select_related(
            'subject', 'grade', 'teacher', 'type'
        )
        data = [
            {
                'id': l.id,
                'day_of_week': l.day_of_week,
                'start_time': l.start_time,
                'duration_minutes': l.duration_minutes,
                'subject': l.subject_id,
                'subject_name': l.subject.name,
                'grade': l.grade_id,
                'grade_name': l.grade.name,
                'teacher': l.teacher_id,
                'teacher_name': f"{l.teacher.last_name} {l.teacher.first_name}",
                'type': l.type.key,
                'type_label': l.type.label
            }
            for l in lessons
        ]
        return Response(data)

# Стандартный CRUD для уроков
class TemplateLessonViewSet(viewsets.ModelViewSet):
    queryset = TemplateLesson.objects.all()
    serializer_class = TemplateLessonSerializer


