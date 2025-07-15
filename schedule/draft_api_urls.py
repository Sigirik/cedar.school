
from rest_framework.routers import DefaultRouter
from .draft_api_views import TemplateWeekDraftViewSet

router = DefaultRouter()
router.register("template-drafts", TemplateWeekDraftViewSet, basename="template-draft")

urlpatterns = router.urls

from .ktp_api_views import SubjectViewSet, GradeViewSet, TeacherViewSet

router.register(r"subjects", SubjectViewSet)
router.register(r"grades", GradeViewSet)
router.register(r"teachers", TeacherViewSet)