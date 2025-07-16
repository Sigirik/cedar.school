from rest_framework.routers import DefaultRouter
from django.urls import path
from .template_api_views import TemplateWeekViewSet, ActiveTemplateWeekView, TeacherAvailabilityViewSet

router = DefaultRouter()
router.register(r'template-week', TemplateWeekViewSet, basename='template-week')
router.register(r'teacher-availability', TeacherAvailabilityViewSet, basename='teacher-availability')

urlpatterns = [
    path('template-week/active/', ActiveTemplateWeekView.as_view(), name='template_week_active'),
] + router.urls