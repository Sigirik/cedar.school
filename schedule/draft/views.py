"""
schedule/draft/views.py
Функции для управления единственным активным черновиком недели (универсально и прозрачно).
"""
from django.utils.timezone import now
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import TemplateWeekDraft
from .serializers import TemplateWeekDraftSerializer
from schedule.core.models import AcademicYear, LessonType
from schedule.template.models import TemplateWeek, TemplateLesson
from django.shortcuts import get_object_or_404
from schedule.validators.schedule_rules import check_collisions
from rest_framework import status

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_or_create_draft(request):
    """
    Получить или создать единственный черновик для пользователя.
    """
    draft, created = TemplateWeekDraft.objects.get_or_create(user=request.user)
    serializer = TemplateWeekDraftSerializer(draft)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_draft_from_template(request):
    """
    Создать новый черновик на основе указанной недели (или активной, если не указано).
    """
    template_id = request.data.get('template_id')
    if template_id:
        template = get_object_or_404(TemplateWeek, pk=template_id)
    else:
        template = TemplateWeek.objects.filter(is_active=True).first()
        if not template:
            return Response({"detail": "Нет активной недели"}, status=400)

    # Удаляем старый черновик пользователя
    TemplateWeekDraft.objects.filter(user=request.user).delete()
    # Готовим уроки (плоская структура)
    lessons = TemplateLesson.objects.filter(template_week=template)
    lessons_data = [
        {
            "id": l.id,
            "subject": l.subject_id,
            "grade": l.grade_id,
            "teacher": l.teacher_id,
            "day_of_week": l.day_of_week,
            "start_time": l.start_time.strftime("%H:%M") if l.start_time else None,
            "duration_minutes": l.duration_minutes,
            "type": l.type.key if l.type else None
        }
        for l in lessons
    ]
    draft = TemplateWeekDraft.objects.create(
        user=request.user,
        base_week=template,
        data={"lessons": lessons_data},
        change_history=[]
    )
    serializer = TemplateWeekDraftSerializer(draft)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_empty_draft(request):
    """
    Создать пустой черновик (без уроков).
    """
    TemplateWeekDraft.objects.filter(user=request.user).delete()
    draft = TemplateWeekDraft.objects.create(
        user=request.user,
        data={"lessons": []},
        change_history=[]
    )
    serializer = TemplateWeekDraftSerializer(draft)
    return Response(serializer.data)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_draft(request):
    """
    Обновить существующий черновик (заменяет lessons целиком).
    """
    draft = get_object_or_404(TemplateWeekDraft, user=request.user)
    changes = request.data.get('data', {})
    draft.change_history.append(draft.data)
    draft.data = changes
    draft.save()
    serializer = TemplateWeekDraftSerializer(draft)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def commit_draft(request):
    """
    Применить черновик (публикация как новой активной недели, сброс черновика).
    """
    draft = get_object_or_404(TemplateWeekDraft, user=request.user)
    lessons = (draft.data or {}).get("lessons", [])

    # Деактивируем все недели
    TemplateWeek.objects.filter(is_active=True).update(is_active=False)
    # Создаём новую активную неделю
    week = TemplateWeek.objects.create(
        name=f"Шаблон от {now().date().isoformat()}",
        academic_year=draft.base_week.academic_year if draft.base_week else AcademicYear.objects.first(),
        is_active=True,
        description="Опубликовано пользователем {}".format(request.user.username)
    )
    print("🔥 COMMIT LESSONS:", lessons)

    for l in lessons:
        # Определяем type_id: сначала берем явный, иначе ищем по ключу
        type_id = l.get("type_id")
        if not type_id:
            type_key = l.get("type")
            if type_key:
                try:
                    type_id = LessonType.objects.only("id").get(key=type_key).id
                except LessonType.DoesNotExist:
                    type_id = None  # оставим пустым, если указан неизвестный ключ

        TemplateLesson.objects.create(
            template_week=week,
            grade_id=l["grade"],
            subject_id=l["subject"],
            teacher_id=l["teacher"],
            day_of_week=l["day_of_week"],
            start_time=l["start_time"],
            duration_minutes=l["duration_minutes"],
            type_id=type_id  # теперь сохраняем тип, если удалось определить
        )

    # Сброс черновика
    draft.data = {"lessons": []}
    draft.change_history = []
    draft.save()
    return Response({"detail": "Черновик опубликован. Неделя создана.", "week_id": week.id})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def draft_exists(request):
    exists = TemplateWeekDraft.objects.filter(user=request.user).exists()
    return Response({ "exists": exists })

# вернёт {lessons, collisions} без коммита.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_draft(request):
    """
    Проверка коллизий без коммита. Возвращает уроки + список проблем.
    """
    draft = get_object_or_404(TemplateWeekDraft, user=request.user)
    lessons = (draft.data or {}).get("lessons", [])
    collisions = check_collisions(lessons)

    return Response({
        "lessons": lessons,       # фронт уже умеет готовить их к UI
        "collisions": collisions  # [{ type, resource_id?, weekday?, lesson_ids, severity, message }]
    }, status=status.HTTP_200_OK)
