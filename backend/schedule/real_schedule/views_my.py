from __future__ import annotations

from django.db.models import Q
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from users.models import User, ParentChild
from schedule.real_schedule.models import RealLesson
from schedule.real_schedule.serializers import MyRealLessonSerializer
from schedule.core.models import StudentSubject
from schedule.core.services import date_windows as dw

ALLOWED_MANAGER_ROLES = {
    User.Role.ADMIN,
    User.Role.DIRECTOR,
    User.Role.HEAD_TEACHER,
    User.Role.AUDITOR,
    User.Role.METHODIST,
}

DEFAULT_PAGE_SIZE = getattr(settings, "REST_FRAMEWORK", {}).get("PAGE_SIZE", 200)

def _filter_for_student(queryset, student: "User"):
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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user: User = request.user

        raw_from = request.query_params.get("from")
        raw_to = request.query_params.get("to")

        if not raw_from and not raw_to:
            d_from, d_to = dw.get_default_school_week()
        else:
            d_from, d_to = dw.parse_from_to_dates(raw_from, raw_to)

        try:
            from_dt, to_dt_excl = dw.validate_and_materialize_range(d_from, d_to)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        qs = (
            RealLesson.objects
            .select_related("subject", "grade", "teacher", "lesson_type")
            .filter(start__gte=from_dt, start__lt=to_dt_excl)
            .order_by("start", "grade_id")
        )

        role = user.role
        if role in ALLOWED_MANAGER_ROLES:
            pass

        elif role == User.Role.TEACHER:
            qs = qs.filter(teacher_id=user.id)

        elif role == User.Role.STUDENT:
            qs = _filter_for_student(qs, user)

        elif role == User.Role.PARENT:
            from users.models import ParentChild
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
                    pass

            if not children:
                qs = qs.none()
            else:
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
            {"from": d_from.isoformat(), "to": d_to.isoformat(), "count": len(data), "results": data},
            status=200,
        )

class RealLessonsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user: User = request.user
        if user.role not in ALLOWED_MANAGER_ROLES:
            return Response({"detail": "FORBIDDEN"}, status=403)

        # Даты
        raw_from = request.query_params.get("from")
        raw_to   = request.query_params.get("to")
        if not raw_from and not raw_to:
            d_from, d_to = dw.get_default_school_week()
        else:
            d_from, d_to = dw.parse_from_to_dates(raw_from, raw_to)

        try:
            from_dt, to_dt_excl = dw.validate_and_materialize_range(d_from, d_to)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        # База
        qs = (
            RealLesson.objects
            .select_related("subject", "grade", "teacher", "lesson_type")
            .filter(start__gte=from_dt, start__lt=to_dt_excl)
        )

        # Фильтры (И)
        def _to_int(name):
            v = request.query_params.get(name)
            if v in (None, "",):
                return None
            try:
                return int(v)
            except Exception:
                raise ValueError(f"INVALID_{name.upper()}")

        try:
            teacher_id = _to_int("teacher_id")
            grade_id   = _to_int("grade_id")
            subject_id = _to_int("subject_id")
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        if teacher_id:
            qs = qs.filter(teacher_id=teacher_id)
        if grade_id:
            qs = qs.filter(grade_id=grade_id)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)

        # Сортировка
        ordering = request.query_params.get("ordering") or "start"
        if ordering == "-start":
            qs = qs.order_by("-start", "grade__name")
        else:
            qs = qs.order_by("start", "grade__name")

        # Пагинация DRF
        paginator = PageNumberPagination()
        try:
            paginator.page_size = int(request.query_params.get("page_size", DEFAULT_PAGE_SIZE))
        except Exception:
            paginator.page_size = DEFAULT_PAGE_SIZE
        page = paginator.paginate_queryset(qs, request, view=self)
        ctx_tz = request.headers.get("X-TZ") or request.query_params.get("tz")
        if page is not None:
            data = MyRealLessonSerializer(page, many=True, context={"tz": ctx_tz}).data
            return paginator.get_paginated_response(data)
        data = MyRealLessonSerializer(qs, many=True, context={"tz": ctx_tz}).data
        return Response({"count": len(data), "next": None, "previous": None, "results": data}, status=200)

class ViewAsScheduleView(APIView):
    """
    Возвращает расписание в ТОМ ЖЕ контракте, что и /api/real_schedule/my/,
    но «как видит» пользователь с id = user_id.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id: int):
        actor: User = request.user
        try:
            target: User = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "NOT_FOUND"}, status=404)

        # Даты
        raw_from = request.query_params.get("from")
        raw_to   = request.query_params.get("to")
        if not raw_from and not raw_to:
            d_from, d_to = dw.get_default_school_week()
        else:
            d_from, d_to = dw.parse_from_to_dates(raw_from, raw_to)

        try:
            from_dt, to_dt_excl = dw.validate_and_materialize_range(d_from, d_to)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        # Право использовать view-as
        def _teacher_can_view_student(teacher: User, student: User) -> bool:
            base = RealLesson.objects.filter(start__gte=from_dt, start__lt=to_dt_excl)
            # уроки студента (по подпискам/классам)
            student_qs = _filter_for_student(base, student)
            return student_qs.filter(teacher_id=teacher.id).exists()

        if actor.role in ALLOWED_MANAGER_ROLES:
            allowed = True
        elif actor.role == User.Role.TEACHER and target.role == User.Role.STUDENT:
            allowed = _teacher_can_view_student(actor, target)
        elif actor.role == User.Role.PARENT and target.role == User.Role.STUDENT:
            allowed = ParentChild.objects.filter(parent=actor, child=target, is_active=True).exists()
        else:
            allowed = False

        if not allowed:
            return Response({"detail": "FORBIDDEN"}, status=403)

        # Считаем расписание ТАК ЖЕ, как в MyScheduleView — но для target
        qs = (
            RealLesson.objects
            .select_related("subject", "grade", "teacher", "lesson_type")
            .filter(start__gte=from_dt, start__lt=to_dt_excl)
        )

        if target.role in ALLOWED_MANAGER_ROLES:
            pass
        elif target.role == User.Role.TEACHER:
            qs = qs.filter(teacher_id=target.id)
        elif target.role == User.Role.STUDENT:
            qs = _filter_for_student(qs, target)
        elif target.role == User.Role.PARENT:
            # агрегируем по всем активным детям родителя
            child_ids = list(
                ParentChild.objects.filter(parent=target, is_active=True).values_list("child_id", flat=True)
            )
            if not child_ids:
                qs = qs.none()
            else:
                cond = Q()
                base = RealLesson.objects.filter(start__gte=from_dt, start__lt=to_dt_excl)
                for cid in child_ids:
                    try:
                        child = User.objects.get(pk=cid)
                    except User.DoesNotExist:
                        continue
                    child_pks = _filter_for_student(base, child).values_list("pk", flat=True)
                    cond |= Q(pk__in=list(child_pks))
                qs = qs.filter(cond)
        else:
            return Response({"detail": "FORBIDDEN"}, status=403)

        qs = qs.order_by("start", "grade__name")
        ctx_tz = request.headers.get("X-TZ") or request.query_params.get("tz")
        data = MyRealLessonSerializer(qs, many=True, context={"tz": ctx_tz}).data
        return Response(
            {"from": d_from.isoformat(), "to": d_to.isoformat(), "count": len(data), "results": data},
            status=200,
        )