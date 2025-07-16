# template_api_views.py — DRF views и viewsets для шаблонной недели

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from datetime import datetime
from schedule.models import TeacherAvailability

from .models import TemplateWeek, TemplateLesson
from .serializers import TemplateWeekSerializer, TemplateWeekDetailSerializer, TeacherAvailabilitySerializer


class ActiveTemplateWeekView(APIView):
    def get(self, request):
        active_week = TemplateWeek.objects.filter(is_active=True).order_by("-created_at").first()
        if not active_week:
            return Response({"detail": "No active template week found."}, status=404)
        data = TemplateWeekDetailSerializer(active_week).data
        return Response(data)

class TeacherAvailabilityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TeacherAvailability.objects.select_related('teacher').all()
    serializer_class = TeacherAvailabilitySerializer


class TemplateWeekViewSet(viewsets.ModelViewSet):
    queryset = TemplateWeek.objects.all()
    serializer_class = TemplateWeekSerializer

    def clone_to_draft_from_instance(self, request, source_week):
        force = request.data.get("force", False)

        existing_draft = TemplateWeek.objects.filter(is_active=False).first()
        if existing_draft:
            if not force:
                return Response({"detail": "draft_exists"}, status=status.HTTP_409_CONFLICT)
            TemplateLesson.objects.filter(template_week=existing_draft).delete()
            draft = existing_draft
        else:
            from datetime import datetime
            draft = TemplateWeek.objects.create(
                school_year=source_week.school_year,
                is_active=False,
                name=f"Черновик от {datetime.today().strftime('%d.%m.%Y')}"
            )

        lessons = TemplateLesson.objects.filter(template_week=source_week)
        for lesson in lessons:
            lesson.pk = None
            lesson.template_week = draft
            lesson.save()

        return Response(TemplateWeekSerializer(draft).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def historical_templates(self, request):
        templates = TemplateWeek.objects.exclude(is_active=True).order_by('-created_at')
        serializer = self.get_serializer(templates, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='active/clone_to_draft')
    def clone_active_to_draft(self, request):
        print("✅ clone_active_to_draft called")
        active_week = TemplateWeek.objects.filter(is_active=True).order_by('-created_at').first()
        if not active_week:
            print("⛔ Нет активной недели")
            return Response({"detail": "Нет активной недели"}, status=404)

        print(f"📦 Активная неделя ID: {active_week.pk}")
        request._full_data = {**request.data}  # копируем force, если нужно
        return self.clone_to_draft_from_instance(request, active_week)

    @action(detail=True, methods=['post'])
    def clone_to_draft(self, request, pk=None):
        print(f"📥 clone_to_draft called with pk={pk}")
        source_week = self.get_object()

        force = request.data.get("force", False)
        existing_draft = TemplateWeek.objects.filter(is_draft=True, school_year=source_week.school_year).first()
        if existing_draft:
            if not force:
                return Response({"detail": "draft_exists"}, status=status.HTTP_409_CONFLICT)
            TemplateLesson.objects.filter(template_week=existing_draft).delete()
            draft = existing_draft
        else:
            date_label = datetime.today().strftime("%d.%m.%Y")
            draft = TemplateWeek.objects.create(
                school_year=source_week.school_year,
                is_draft=True,
                name=f"Черновик от {date_label}"
            )
            print(f"✏️ Создаём черновик: {draft}")

        lessons = TemplateLesson.objects.filter(template_week=source_week)
        for lesson in lessons:
            lesson.pk = None
            lesson.template_week = draft
            lesson.save()

        return Response(TemplateWeekSerializer(draft).data, status=status.HTTP_201_CREATED)
