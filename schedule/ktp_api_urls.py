# ktp_api_urls.py — только маршруты, относящиеся к КТП и справочникам

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .ktp_api_views import (
    KTPTemplateViewSet,
    KTPSectionViewSet,
    KTPEntryViewSet,
    SubjectViewSet,
    GradeViewSet,
    TeacherViewSet,
    WeeklyNormViewSet,
)

router = DefaultRouter()
router.register(r'ktp-templates', KTPTemplateViewSet)
router.register(r'ktp-sections', KTPSectionViewSet)
router.register(r'ktp-entries', KTPEntryViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'grades', GradeViewSet)
router.register(r'teachers', TeacherViewSet)
router.register(r'weekly-norms', WeeklyNormViewSet)

urlpatterns = router.urls
