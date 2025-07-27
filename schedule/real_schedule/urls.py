from rest_framework.routers import DefaultRouter
from .views import RealLessonViewSet

router = DefaultRouter()
router.register(r'lessons', RealLessonViewSet)

urlpatterns = router.urls