# backend/schedule/real_schedule/permissions.py
from rest_framework.permissions import BasePermission
from django.apps import apps
from schedule.core.models import StudentSubject  # опираемся на ваши справочники
from users.models import ParentChild                     # <— ДОБАВЬ
# при желании можно импортировать TeacherGrade/TeacherSubject/GradeSubject,
# но для доступа учителя они не используются

ROLE_ADMIN = "ADMIN"
ROLE_HEAD  = "HEAD_TEACHER"
ROLE_DIR   = "DIRECTOR"
ROLE_MET = "METHODIST"
ROLE_AUD = "AUDITOR"
ROLE_TEACH = "TEACHER"
ROLE_STUD  = "STUDENT"
ROLE_PAR   = "PARENT"

def _lesson_has_student(lesson, user_id: int) -> bool:
    # Индивидуальная привязка ученика к уроку, если такая M2M используется
    for attr in ("students", "individual_students", "student_users"):
        mgr = getattr(lesson, attr, None)
        if mgr is None:
            continue
        if hasattr(mgr, "filter"):
            try:
                return mgr.filter(pk=user_id).exists()
            except Exception:
                pass
        try:
            return any(getattr(s, "id", None) == user_id for s in list(mgr))
        except Exception:
            continue
    return False

def _parent_children_ids_and_grades(user):
    child_ids, child_grade_ids = set(), set()
    pp = getattr(user, "parent_profile", None)
    if pp and hasattr(pp, "children"):
        try:
            for sp in pp.children.all():  # StudentProfile
                if getattr(sp, "user_id", None):
                    child_ids.add(sp.user_id)
                if getattr(sp, "grade_id", None):
                    child_grade_ids.add(sp.grade_id)
        except Exception:
            pass
    if pp and hasattr(pp, "child_users"):
        try:
            for cu in pp.child_users.all():  # User
                child_ids.add(cu.id)
                sp = getattr(cu, "student_profile", None)
                if sp and getattr(sp, "grade_id", None):
                    child_grade_ids.add(sp.grade_id)
        except Exception:
            pass
    # возможный фолбэк из старого кода
    for gid in getattr(user, "child_grade_ids", []) or []:
        if gid is not None:
            child_grade_ids.add(gid)
    return child_ids, child_grade_ids

def _get_child_ids(parent_user):
    """Активные дети родителя по модели ParentChild."""
    return set(
        ParentChild.objects.filter(parent=parent_user, is_active=True)
        .values_list("child_id", flat=True)
    )

class CanViewLesson(BasePermission):
    def has_permission(self, request, view):
        return bool(getattr(request, "user", None) and request.user.is_authenticated)

    def has_object_permission(self, request, view, lesson):
        user = request.user
        role = getattr(user, "role", None)

        if role in (ROLE_ADMIN, ROLE_HEAD, ROLE_DIR, ROLE_MET, ROLE_AUD):
            return True

        if role == ROLE_TEACH:
            if lesson.teacher_id == user.id:
                return True
            co = getattr(lesson, "co_teachers", None)
            if co is not None:
                try:
                    return co.filter(pk=user.id).exists()
                except Exception:
                    pass
            return False

        if role == ROLE_STUD:
            # подписка на предмет + класс
            if StudentSubject.objects.filter(
                student=user, grade_id=lesson.grade_id, subject_id=lesson.subject_id
            ).exists():
                return True
            # индивидуально добавлен
            return _lesson_has_student(lesson, user.id)

        if role == ROLE_PAR:
            child_ids = _get_child_ids(user)
            if not child_ids:
                return False

            # 1) ребёнок подписан на предмет этого урока
            if StudentSubject.objects.filter(
                student_id__in=child_ids,
                grade_id=lesson.grade_id,
                subject_id=lesson.subject_id,
            ).exists():
                return True

            # 2) ребёнок индивидуально добавлен на урок (LessonStudent / M2M)
            try:
                LessonStudent = apps.get_model("real_schedule", "LessonStudent")
                if LessonStudent.objects.filter(lesson_id=lesson.id, student_id__in=child_ids).exists():
                    return True
            except LookupError:
                pass

            for cid in child_ids:
                if _lesson_has_student(lesson, cid):
                    return True

            return False

        return False
