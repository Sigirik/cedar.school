from rest_framework.routers import DefaultRouter
from django.urls import path
from .draft_api_views import (
    TemplateWeekDraftViewSet,
    create_draft_from_template,
    create_empty_draft,
)

router = DefaultRouter()
router.register("template-drafts", TemplateWeekDraftViewSet, basename="template-draft")

urlpatterns = [
    path("template-drafts/create-from/<int:template_id>/", create_draft_from_template),
    path("template-drafts/create-empty/", create_empty_draft),
] + router.urls