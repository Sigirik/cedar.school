"""
Модуль ktp/urls.py:
Маршруты API для календарно-тематических планов.
"""

from rest_framework.routers import DefaultRouter
from .views import KTPTemplateViewSet, KTPSectionViewSet, KTPEntryViewSet

router = DefaultRouter()
router.register(r'templates', KTPTemplateViewSet)
router.register(r'sections', KTPSectionViewSet)
router.register(r'entries', KTPEntryViewSet)

urlpatterns = router.urls