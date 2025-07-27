"""
Модуль template/urls.py:
Маршруты API для работы с шаблонными неделями и уроками.
"""

from rest_framework.routers import SimpleRouter
from .views import TemplateWeekViewSet, TemplateLessonViewSet
from django.urls import path

router = SimpleRouter()
router.register('weeks', TemplateWeekViewSet)
router.register('lessons', TemplateLessonViewSet)

urlpatterns = [
    *router.urls,
    path('active-week/', TemplateWeekViewSet.as_view({'get': 'active'}), name='active-week'),
]
