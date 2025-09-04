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
      - иначе -> фильтруем по классу(ам) ученика (если они заданы через StudentSubject).
    """
    if getattr(student, "individual_subjects_enabled", False):
        subject_ids = (StudentSubject.objects
                       .filter(student=student)
                       .values_list("subject_id", flat=True)
                       .distinct())
        return queryset.filter(subject_id__in=subject_ids)

    # Без индивидуального режима: фильтрация по классам ученика.
    # Так как поля user.grade нет, берём классы из StudentSubject.
    grade_ids = (StudentSubject.objects
                 .filter(student=student)
                 .values_list("grade_id", flat=True)
                 .distinct())

    # Если класс(ы) не заданы — ничего не возвращаем.
    return queryset.filter(grade_id__in=grade_ids) if grade_ids else queryset.none()


class MyScheduleView(APIView):
    """
    GET /api/real_schedule/my/?from=&to=
    Правила доступа: IsAuthenticated. Фильтрация по роли.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user: User = request.user

<<<<<<< Updated upstream
        # 1) Определяем интервал
=======
        # Параметры периода
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
        # 2) Базовый queryset
=======
        # База выборки
>>>>>>> Stashed changes
        qs = (
            RealLesson.objects
            .select_related("subject", "grade", "teacher", "lesson_type")
            .filter(start__gte=from_dt, start__lt=to_dt_excl)
            .order_by("start", "grade_id")
        )

        # 3) Ролевая фильтрация
        role = user.role

        if role in ALLOWED_ADMIN_ROLES:
<<<<<<< Updated upstream
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
=======
            pass

        elif role == User.Role.TEACHER:
            qs = qs.filter(teacher_id=user.id)

        elif role == User.Role.STUDENT:
            # Единая функция: в индивидуальном режиме класс не учитываем (только предметы),
            # иначе фильтруем по классам ученика (из StudentSubject).
            qs = _filter_for_student(qs, user)

        elif role == User.Role.PARENT:
            # Через users.ParentChild; агрегируем расписание детей теми же правилами, что и для STUDENT.
            from users.models import ParentChild  # локальный импорт, чтобы избежать циклов при миграциях

            links = (
                ParentChild.objects
                .filter(parent=user, is_active=True)
                .select_related("child")
            )
            children = [ln.child for ln in links]

            # Опционально: ?children=12,34 — вручную ограничить детей
            children_param = request.query_params.get("children")
            if children_param:
                try:
                    allowed_ids = {int(x) for x in children_param.split(",") if x.strip().isdigit()}
                    children = [c for c in children if c.id in allowed_ids]
                except Exception:
                    # игнорируем некорректный параметр
                    pass

            if not children:
                qs = qs.none()
            else:
                # Объединяем условия по каждому ребёнку; для детей в индивидуальном режиме
                # класс не ограничивает выборку — фильтрация только по предметам.
                cond = Q()
                base = RealLesson.objects.filter(start__gte=from_dt, start__lt=to_dt_excl)
                for child in children:
                    child_pks = _filter_for_student(base, child).values_list("pk", flat=True)
                    cond |= Q(pk__in=list(child_pks))
                qs = qs.filter(cond)

>>>>>>> Stashed changes
        else:
            # неизвестная/служебная роль — запретим
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
