# backend/schedule/real_schedule/permissions.py
from rest_framework.permissions import BasePermission
from schedule.core.models import StudentSubject  # опираемся на ваши справочники
# при желании можно импортировать TeacherGrade/TeacherSubject/GradeSubject,
# но для доступа учителя они не используются

ROLE_ADMIN = "ADMIN"
ROLE_HEAD  = "HEAD_TEACHER"
ROLE_DIR   = "DIRECTOR"
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

class CanViewLesson(BasePermission):
    """
    Строгие объектные права:
      - Ученики/родители видят урок только при подписке на предмет (grade+subject) или индивидуальной привязке.
      - Учителя — только если назначены на урок.
    """

    def has_permission(self, request, view):
        return bool(getattr(request, "user", None) and request.user.is_authenticated)

    def has_object_permission(self, request, view, lesson):
        user = request.user
        role = getattr(user, "role", None)

        if role in (ROLE_ADMIN, ROLE_HEAD, ROLE_DIR):
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
            # Подписка ученика на предмет (в рамках класса)
            if StudentSubject.objects.filter(
                student=user,
                grade_id=lesson.grade_id,
                subject_id=lesson.subject_id
            ).exists():
                return True
            # Индивидуальная привязка к уроку
            return _lesson_has_student(lesson, user.id)

        if role == ROLE_PAR:
            child_ids, child_grade_ids = _parent_children_ids_and_grades(user)
            # Подписка любого ребёнка на предмет этого урока
            if StudentSubject.objects.filter(
                student_id__in=list(child_ids) or [-1],
                grade_id=lesson.grade_id,
                subject_id=lesson.subject_id
            ).exists():
                return True
            # Индивидуальная привязка ребёнка к уроку
            for cid in child_ids:
                if _lesson_has_student(lesson, cid):
                    return True
            return False

        return False
