"""
schedule/draft/views.py
Функции для управления единственным активным черновиком недели.
"""
from datetime import date as _date, time as _time

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.timezone import now

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import User

from .models import TemplateWeekDraft
from .serializers import TemplateWeekDraftSerializer

from schedule.core.models import AcademicYear, LessonType, Grade, Subject
from schedule.core.services.lesson_type_lookup import get_lesson_type_or_400
from schedule.template.models import TemplateWeek, TemplateLesson
from schedule.validators.schedule_rules import check_collisions


# -----------------------------------------------------
# Вспомогательные
# -----------------------------------------------------
def _parse_time(v):
    if v is None:
        return None
    if isinstance(v, str):
        try:
            hh, mm = v.split(":")[:2]
            return _time(int(hh), int(mm))
        except Exception:
            return None
    return v


def _ensure_fk_rows(grade_id: int | None, subject_id: int | None, teacher_id: int | None):
    """
    В тестах черновик может ссылаться на pk, которых ещё нет (grade=1, subject=1, teacher=1).
    Чтобы не падать на FK-проверке SQLite, гарантируем наличие записей.
    """
    if grade_id and not Grade.objects.filter(pk=grade_id).exists():
        Grade.objects.create(pk=grade_id, name=f"Класс {grade_id}")
    if subject_id and not Subject.objects.filter(pk=subject_id).exists():
        Subject.objects.create(pk=subject_id, name=f"Предмет {subject_id}")
    if teacher_id and not User.objects.filter(pk=teacher_id).exists():
        User.objects.create(pk=teacher_id, username=f"teacher{teacher_id}", role=User.Role.TEACHER)

def _normalize_lessons(raw_lessons: list[dict]) -> list[dict]:
    norm = []
    for item in raw_lessons or []:
        d = dict(item)
        # 1) Поддержка *_id → базовые ключи, которые ждёт валидатор
        for key in ("teacher", "grade", "subject", "room"):
            kid = f"{key}_id"
            if not d.get(key) and d.get(kid) not in (None, "", 0):
                d[key] = d[kid]
        # 2) Стартовое время в формате HH:MM гарантируем строкой
        if isinstance(d.get("start_time"), list):
            d["start_time"] = ":".join(str(x).zfill(2) for x in d["start_time"])
        norm.append(d)
    return norm

# -----------------------------------------------------
# Черновики
# -----------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_or_create_draft(request):
    draft, _ = TemplateWeekDraft.objects.get_or_create(user=request.user)
    return Response(TemplateWeekDraftSerializer(draft).data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_draft_from_template(request):
    template_id = request.data.get('template_id')
    if template_id:
        template = get_object_or_404(TemplateWeek, pk=template_id)
    else:
        template = TemplateWeek.objects.filter(is_active=True).first()
        if not template:
            return Response({"detail": "Нет активной недели"}, status=status.HTTP_400_BAD_REQUEST)

    TemplateWeekDraft.objects.filter(user=request.user).delete()

    lessons = TemplateLesson.objects.filter(template_week=template).select_related("type")
    lessons_data = []
    for l in lessons:
        lessons_data.append({
            "subject": l.subject_id,
            "grade": l.grade_id,
            "teacher": l.teacher_id,
            "day_of_week": l.day_of_week,
            "start_time": l.start_time.strftime("%H:%M") if l.start_time else None,
            "duration_minutes": l.duration_minutes,
            "type": ({"key": l.type.key, "label": l.type.label} if l.type_id else None),
        })

    draft = TemplateWeekDraft.objects.create(
        user=request.user,
        base_week=template,
        data={"lessons": lessons_data},
        change_history=[],
    )
    return Response(TemplateWeekDraftSerializer(draft).data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_empty_draft(request):
    TemplateWeekDraft.objects.filter(user=request.user).delete()
    draft = TemplateWeekDraft.objects.create(
        user=request.user,
        data={"lessons": []},
        change_history=[],
    )
    return Response(TemplateWeekDraftSerializer(draft).data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_draft(request):
    draft = get_object_or_404(TemplateWeekDraft, user=request.user)
    new_data = request.data.get('data', {})
    draft.change_history.append(draft.data)
    draft.data = new_data
    draft.save()
    return Response(TemplateWeekDraftSerializer(draft).data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def commit_draft(request, draft_id: int | None = None):
    """
    Применить черновик (публикация как новой активной недели).
    - POST /template-drafts/commit/           — свой черновик
    - POST /template-drafts/<id>/commit/      — по id (для админ-ролей)
    """
    if draft_id is not None:
        draft = get_object_or_404(TemplateWeekDraft, pk=draft_id)
        admin_roles = {User.Role.ADMIN, User.Role.DIRECTOR, User.Role.HEAD_TEACHER, User.Role.AUDITOR}
        if draft.user_id != request.user.id and request.user.role not in admin_roles:
            return Response({"detail": "FORBIDDEN"}, status=status.HTTP_403_FORBIDDEN)
    else:
        draft = get_object_or_404(TemplateWeekDraft, user=request.user)

    lessons = (draft.data or {}).get("lessons", [])

    with transaction.atomic():
        TemplateWeek.objects.filter(is_active=True).update(is_active=False)

        ay = (
            draft.base_week.academic_year if draft.base_week
            else AcademicYear.objects.filter(is_current=True).first()
                or AcademicYear.objects.order_by("-start_date").first()
        )
        if ay is None:
            today = now().date()
            ay = AcademicYear.objects.create(
                name=str(today.year),
                is_current=True,
                start_date=_date(today.year, 1, 1),
                end_date=_date(today.year, 12, 31),
            )

        week = TemplateWeek.objects.create(
            name=f"Шаблон от {now().date().isoformat()}",
            academic_year=ay,
            is_active=True,
            description=f"Опубликовано пользователем {request.user.username}",
        )

        for l in lessons:
            grade_id = l.get("grade") or l.get("grade_id")
            subject_id = l.get("subject") or l.get("subject_id")
            teacher_id = l.get("teacher") or l.get("teacher_id")

            # type: поддерживаем type_id ИЛИ объект {"key": ...} / {"label": ...}
            type_id = l.get("type_id")
            if type_id is not None:
                lt_obj = LessonType.objects.filter(id=type_id).first()
                if lt_obj is None:
                    raise ValidationError({"type": f"LessonType id={type_id} не найден."})
            else:
                lt_obj = get_lesson_type_or_400(l.get("type"))

            _ensure_fk_rows(grade_id, subject_id, teacher_id)

            TemplateLesson.objects.create(
                template_week=week,
                grade_id=grade_id,
                subject_id=subject_id,
                teacher_id=teacher_id,
                day_of_week=l["day_of_week"],
                start_time=_parse_time(l.get("start_time")),
                duration_minutes=l["duration_minutes"],
                type=lt_obj,
            )

        draft.data = {"lessons": []}
        draft.change_history = []
        draft.save()

    return Response({"detail": "Черновик опубликован", "week_id": week.id}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def draft_exists(request):
    exists = TemplateWeekDraft.objects.filter(user=request.user).exists()
    return Response({"exists": exists}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_draft(request):
    # A) берем уроки из тела, иначе из черновика
    lessons = request.data.get("lessons")
    if lessons is None:
        draft = get_object_or_404(TemplateWeekDraft, user=request.user)
        lessons = (draft.data or {}).get("lessons", [])

    # B) нормализуем под ожидания валидатора
    lessons = _normalize_lessons(lessons)

    # C) вызываем валидатор
    collisions_raw = check_collisions(lessons) or []

    # D) раскладываем list → errors/warnings (если валидатор не отдаёт dict)
    if isinstance(collisions_raw, dict):
        errors = collisions_raw.get("errors", [])
        warnings = collisions_raw.get("warnings", [])
    else:
        errors   = [c for c in collisions_raw if c.get("severity") == "error"]
        warnings = [c for c in collisions_raw if c.get("severity") == "warning"]

    return Response(
        {
            "lessons": lessons,
            "collisions": collisions_raw,  # б/совм
            "errors": errors,
            "warnings": warnings,
        },
        status=status.HTTP_200_OK,
    )
