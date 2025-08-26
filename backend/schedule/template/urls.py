"""
Модуль template/urls.py:
Маршруты API для работы с шаблонными неделями и уроками.
"""

from rest_framework.routers import SimpleRouter
from .views import TemplateWeekViewSet, TemplateLessonViewSet
from django.urls import path


router = SimpleRouter()
router.register(r'weeks', TemplateWeekViewSet, basename='templateweek')

urlpatterns = [
    # Активная неделя
    path('active-week/', TemplateWeekViewSet.as_view({'get': 'active_week'}), name='active-week'),
]

urlpatterns += router.urls
