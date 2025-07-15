
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import TemplateWeekDraft, TemplateWeek, TemplateLesson
from .serializers import TemplateWeekDraftSerializer, TemplateWeekDetailSerializer


class TemplateWeekDraftViewSet(viewsets.ModelViewSet):
    queryset = TemplateWeekDraft.objects.all()
    serializer_class = TemplateWeekDraftSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TemplateWeekDraft.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def commit(self, request, pk=None):
        draft = self.get_object()

        # Деактивируем текущий шаблон
        TemplateWeek.objects.filter(is_active=True).update(is_active=False)

        # Сохраняем новый как активный
        new_week = TemplateWeek.objects.create(
            name=f"Шаблонная неделя (версия от {timezone.now().date()})",
            academic_year=draft.base_week.academic_year,
            is_active=True,
            created_at=timezone.now(),
        )

        # Применяем уроки
        lessons = draft.data.get("lessons", [])
        for item in lessons:
            TemplateLesson.objects.create(
                template_week=new_week,
                subject_id=item["subject"],
                grade_id=item["grade"],
                teacher_id=item["teacher"],
                day_of_week=item["day_of_week"],
                start_time=item["start_time"],
                duration_minutes=item["duration_minutes"],
            )

        draft.delete()

        return Response({"message": "Шаблон успешно сохранён как новая активная версия."}, status=status.HTTP_201_CREATED)

from rest_framework.decorators import api_view


@api_view(["GET"])
def active_template_week(request):
    active = TemplateWeek.objects.filter(is_active=True).first()
    if not active:
        return Response({"detail": "Нет активной недели."}, status=404)
    return Response(TemplateWeekDetailSerializer(active).data)

@api_view(["POST"])
def create_draft_from_template(request, template_id):
    template = get_object_or_404(TemplateWeek, id=template_id)
    draft = TemplateWeekDraft.objects.create(
        base_week=template.id,
        data={"lessons": TemplateLessonSerializer(template.lessons.all(), many=True).data}
    )
    return Response(TemplateWeekDraftSerializer(draft).data, status=201)

@api_view(["POST"])
def create_empty_draft(request):
    draft = TemplateWeekDraft.objects.create(
        base_week=None,
        data={"lessons": []}
    )
    return Response(TemplateWeekDraftSerializer(draft).data, status=201)