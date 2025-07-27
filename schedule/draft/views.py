"""
Функции для управления единственным активным черновиком недели.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import TemplateWeekDraft
from .serializers import TemplateWeekDraftSerializer
from schedule.template.models import TemplateWeek
from django.shortcuts import get_object_or_404


@api_view(['GET', 'PATCH', 'POST'])
@permission_classes([IsAuthenticated])
def active_draft(request):
    # получаем или создаём единственный черновик для текущего пользователя
    draft, created = TemplateWeekDraft.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        serializer = TemplateWeekDraftSerializer(draft)
        return Response(serializer.data)

    if request.method == 'PATCH':
        changes = request.data.get('data', {})
        # сохраняем историю
        draft.change_history.append(draft.data)
        draft.data = changes
        draft.save()
        serializer = TemplateWeekDraftSerializer(draft)
        return Response(serializer.data)

    if request.method == 'POST':
        # reset черновика
        template_id = request.data.get('template_id')
        if template_id:
            template = get_object_or_404(TemplateWeek, pk=template_id)
            draft.base_week = template
        draft.data = {}
        draft.change_history = []
        draft.save()
        serializer = TemplateWeekDraftSerializer(draft)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def commit_active_draft(request):
    draft = get_object_or_404(TemplateWeekDraft, user=request.user)
    # логика применения, например, переносит в активную неделю
    # очищаем черновик:
    draft.data = {}
    draft.change_history = []
    draft.save()
    return Response({"detail": "Черновик применён и очищен."})

