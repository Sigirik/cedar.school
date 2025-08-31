# backend/schedule/real_schedule/views_my.py
from __future__ import annotations

import datetime as dt
from typing import Optional, Iterable

from django.db.models import Q
from django.utils import timezone
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


ALLOWED_ADMIN_ROLES = {
    getattr(User.Role, "ADMIN", "ADMIN"),
    getattr(User.Role, "DIRECTOR", "DIRECTOR"),
    getattr(User.Role, "HEAD_TEACHER", "HEAD_TEACHER"),
    getattr(User.Role, "AUDITOR", "AUDITOR"),
}


class MyScheduleView(APIView):
    """
    GET /api/real_schedule/my/?from=&to=
    Правила доступа: IsAuthenticated. Фильтрация по роли.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user: User = request.user

        # 1) Определяем интервал
        raw_from = request.query_params.get("from")
        raw_to   = request.query_params.get("to")

        if not raw_from and not raw_to:
            d_from, d_to = get_default_school_week()  # (date, date)
        else:
            d_from, d_to = parse_from_to_dates(raw_from, raw_to)

        try:
            from_dt, to_dt_excl = validate_and_materialize_range(d_from, d_to)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        # 2) Базовый queryset
        qs = (
            RealLesson.objects
            .select_related("subject", "grade", "teacher", "lesson_type")
            .filter(start__gte=from_dt, start__lt=to_dt_excl)
            .order_by("start", "grade_id")
        )

        # 3) Ролевая фильтрация
        role = user.role

        if role in ALLOWED_ADMIN_ROLES:
            pass  # все уроки
        elif role == getattr(User.Role, "TEACHER", "TEACHER"):
            qs = qs.filter(teacher_id=user.id)
        elif role == getattr(User.Role, "STUDENT", "STUDENT"):
            # 3a) если у пользователя есть grade/grade_id — фильтруем по нему
            user_grade_id = getattr(user, "grade_id", None)
            if user_grade_id:
                qs = qs.filter(grade_id=user_grade_id)
            else:
                # 3b) иначе используем индивидуальные предметы ученика
                ss_qs = StudentSubject.objects.filter(student=user)
                grade_ids = list(ss_qs.values_list("grade_id", flat=True).distinct())
                if not grade_ids:
                    # нет информации о классе — вернём пустой список, но это сигнал к настройке профиля
                    qs = qs.none()
                else:
                    qs = qs.filter(grade_id__in=grade_ids)
                    # если включён индивидуальный выбор — сужаем по предметам, иначе оставляем все предметы класса
                    if getattr(user, "individual_subjects_enabled", False):
                        subj_ids = list(ss_qs.values_list("subject_id", flat=True).distinct())
                        if subj_ids:
                            qs = qs.filter(subject_id__in=subj_ids)
        elif role == getattr(User.Role, "PARENT", "PARENT"):
            # Требуется связь "родитель -> дети". В текущей модели её нет — возвращаем 400.
            return Response({"detail": "PARENT_CHILD_RELATION_MISSING"}, status=400)
        else:
            # неизвестная/служебная роль — запретим
            return Response({"detail": "FORBIDDEN"}, status=403)

        data = MyRealLessonSerializer(qs, many=True).data
        return Response({
            "from": d_from.isoformat(),
            "to": d_to.isoformat(),
            "count": len(data),
            "results": data,
        }, status=200)
