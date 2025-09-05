from __future__ import annotations

from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from users.models import User
from schedule.real_schedule.models import RealLesson
from schedule.real_schedule.serializers import MyRealLessonSerializer
from schedule.core.models import StudentSubject
from schedule.core.services.date_windows import (
    get_default_school_week,
    parse_from_to_dates,
    validate_and_materialize_range,
)

# Админские роли видят всё
ALLOWED_ADMIN_ROLES = {
    User.Role.ADMIN,
    User.Role.DIRECTOR,
    User.Role.HEAD_TEACHER,
    User.Role.AUDITOR,
}

def _filter_for_student(queryset, student: "User"):
    """
    Возвращает queryset RealLesson, отфильтрованный для конкретного ученика.
    Логика:
      - если у ученика включён режим индивидуальных предметов -> фильтруем только по предметам (grade игнорируем);
      - иначе -> фильтруем по классам ученика (классы берём из StudentSubject).
    """
    if getattr(student, "individual_subjects_enabled", False):
        subject_ids = (StudentSubject.objects
                       .filter(student=student)
                       .values_list("subject_id", flat=True)
                       .distinct())
        return queryset.filter(subject_id__in=subject_ids)

    grade_ids = (StudentSubject.objects
                 .filter(student=student)
                 .values_list("grade_id", flat=True)
                 .distinct())

    return queryset.filter(grade_id__in=grade_ids) if grade_ids else queryset.none()


class MyScheduleView(APIView):
    """
    GET /api/real_schedule/my/?from=&to=
    Правила доступа: IsAuthenticated. Фильтрация по роли.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user: User = request.user

        # Параметры периода
        raw_from = request.query_params.get("from")
        raw_to = request.query_params.get("to")

        if not raw_from and not raw_to:
            d_from, d_to = get_default_school_week()  # (date, date)
        else:
            d_from, d_to = parse_from_to_dates(raw_from, raw_to)

        try:
            from_dt, to_dt_excl = validate_and_materialize_range(d_from, d_to)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        # Базовая выборка
        qs = (
            RealLesson.objects
            .select_related("subject", "grade", "teacher", "lesson_type")
            .filter(start__gte=from_dt, start__lt=to_dt_excl)
            .order_by("start", "grade_id")
        )

        # Ролевая фильтрация
        role = user.role

        if role in ALLOWED_ADMIN_ROLES:
            pass  # админы видят всё

        elif role == User.Role.TEACHER:
            qs = qs.filter(teacher_id=user.id)

        elif role == User.Role.STUDENT:
            qs = _filter_for_student(qs, user)

        elif role == User.Role.PARENT:
            # Агрегируем расписание детей (по связкам ParentChild); поддерживаем ?children=1,2
            from users.models import ParentChild  # локальный импорт, чтобы не плодить циклы

            links = (
                ParentChild.objects
                .filter(parent=user, is_active=True)
                .select_related("child")
            )
            children = [ln.child for ln in links]

            children_param = request.query_params.get("children")
            if children_param:
                try:
                    allowed_ids = {int(x) for x in children_param.split(",") if x.strip().isdigit()}
                    children = [c for c in children if c.id in allowed_ids]
                except Exception:
                    pass  # игнорируем некорректный параметр

            if not children:
                qs = qs.none()
            else:
                # Объединяем по PK уроков, прошедших фильтрацию для каждого ребёнка
                cond = Q()
                base = RealLesson.objects.filter(start__gte=from_dt, start__lt=to_dt_excl)
                for child in children:
                    child_pks = _filter_for_student(base, child).values_list("pk", flat=True)
                    cond |= Q(pk__in=list(child_pks))
                qs = qs.filter(cond)

        else:
            return Response({"detail": "FORBIDDEN"}, status=403)

        data = MyRealLessonSerializer(qs, many=True).data
        return Response(
            {
                "from": d_from.isoformat(),
                "to": d_to.isoformat(),
                "count": len(data),
                "results": data,
            },
            status=200,
        )
