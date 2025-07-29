from django.urls import path
from .views import dashboard
from rest_framework.routers import SimpleRouter
from .views import UserViewSet, TeacherViewSet, StudentViewSet

urlpatterns = [
    path("dashboard/", dashboard, name="dashboard"),
]

router = SimpleRouter()
router.register('teachers', TeacherViewSet, basename='teacher')
router.register('students', StudentViewSet, basename='student')
router.register('', UserViewSet, basename='user')


urlpatterns = router.urls