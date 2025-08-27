"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Админка Django
    path("admin/", admin.site.urls),

    # DRF browsable API auth (опционально)
    path("api-auth/", include("rest_framework.urls")),

    # Бизнес-модули
    path("api/core/", include("schedule.core.urls")),
    path("api/template/", include("schedule.template.urls")),
    path("api/draft/", include("schedule.draft.urls")),
    path("api/ktp/", include("schedule.ktp.urls")),
    path("api/real_schedule/", include("schedule.real_schedule.urls")),

    # Пользователи/роли/заявки:
    # внутри users.urls регистрируются роутеры:
    #   /users/, /teachers/, /students/, /role-requests/, ...
    # поэтому префикс ДОЛЖЕН быть "api/", а не "api/users/"
    path("api/", include("users.urls")),

    # Аутентификация Djoser + JWT (логин/рефреш/текущий пользователь)
    #   POST /api/auth/jwt/create/
    #   POST /api/auth/jwt/refresh/
    #   GET  /api/auth/users/me/
    path("api/auth/", include("djoser.urls")),
    path("api/auth/", include("djoser.urls.jwt")),

    # Классические Django auth-вьюхи (если нужны)
    path("accounts/", include("django.contrib.auth.urls")),

    # Если используешь свой CSRF-exempt регистратор — оставь, он не должен конфликтовать
    # (ожидается, что внутри только, например, path("register/", CsrfExemptRegisterView.as_view()))
    path("api/auth/", include("users.registration_urls")),
]
