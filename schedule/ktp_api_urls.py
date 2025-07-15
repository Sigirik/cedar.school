from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .ktp_api_views import KTPTemplateViewSet, KTPSectionViewSet, KTPEntryViewSet, SubjectViewSet, GradeViewSet, TeacherViewSet, WeeklyNormViewSet
from .draft_api_views import TemplateWeekDraftViewSet, active_template_week, create_draft_from_template, create_empty_draft


router = DefaultRouter()
router.register(r'ktp-templates', KTPTemplateViewSet)
router.register(r'ktp-sections', KTPSectionViewSet)
router.register(r'ktp-entries', KTPEntryViewSet)
router.register(r'template-drafts', TemplateWeekDraftViewSet, basename='template-draft')
router.register(r"subjects", SubjectViewSet)
router.register(r"grades", GradeViewSet)
router.register(r"teachers", TeacherViewSet)
router.register(r"weekly-norms", WeeklyNormViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('template-week/active/', active_template_week, name='template_week_active'),
    path("template-drafts/create-from/<int:template_id>/", create_draft_from_template),
    path("template-drafts/create-empty/", create_empty_draft),
]