from django.urls import path
from .views import template_week_view

urlpatterns = [
    path("", template_week_view),  # ← этот путь
    path("template-week/", template_week_view, name="template_week"),
]