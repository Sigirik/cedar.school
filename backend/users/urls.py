# users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    dashboard,
    UserViewSet,
    TeacherViewSet,
    StudentViewSet,
    RoleRequestViewSet,
    me,  # ← добавим вью ниже
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'teachers', TeacherViewSet, basename='teacher')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'role-requests', RoleRequestViewSet, basename='role-request')

urlpatterns = [
    # API-роуты от viewsets:
    #   /api/users/
    #   /api/teachers/
    #   /api/students/
    #   /api/role-requests/
    #   /api/role-requests/allowed-roles/  ← это приходит из @action allowed_roles
    path('', include(router.urls)),

    # Тонкий "кто я?" (если фронту удобен именно /api/users/me/)
    path('users/me/', me),

    # Серверный дашборд (будет /api/dashboard/)
    path('dashboard/', dashboard, name='dashboard'),
]
