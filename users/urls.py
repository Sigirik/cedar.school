from django.urls import path
from .views import dashboard
from rest_framework.routers import SimpleRouter
from .views import UserViewSet

urlpatterns = [
    path("dashboard/", dashboard, name="dashboard"),
]

router = SimpleRouter()
router.register('users', UserViewSet)

urlpatterns = router.urls