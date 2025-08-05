"""
Модуль core/urls.py:
Маршруты API для доступа к справочникам core.
"""

from rest_framework.routers import SimpleRouter
from .views import (
    GradeViewSet, SubjectViewSet, TeacherAvailabilityViewSet,
    WeeklyNormViewSet, LessonTypeViewSet, AcademicYearViewSet,
    GradeSubjectViewSet, StudentSubjectViewSet,
    TeacherSubjectViewSet, TeacherGradeViewSet,
    QuarterViewSet, HolidayViewSet
)

router = SimpleRouter()
router.register('grades', GradeViewSet)
router.register('subjects', SubjectViewSet)
router.register('availabilities', TeacherAvailabilityViewSet)
router.register('weekly-norms', WeeklyNormViewSet)
router.register('lesson-types', LessonTypeViewSet)
router.register('academic-years', AcademicYearViewSet)
router.register('grade-subjects', GradeSubjectViewSet)
router.register('teacher-subjects', TeacherSubjectViewSet)
router.register('teacher-grades', TeacherGradeViewSet)
router.register('student-subjects', StudentSubjectViewSet)
router.register("quarters", QuarterViewSet)
router.register("holidays", HolidayViewSet)

urlpatterns = router.urls

