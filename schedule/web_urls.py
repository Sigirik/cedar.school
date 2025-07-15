from django.urls import path, include
from .web_views import (
    template_week_view,
    real_lesson_create_view,
    real_lesson_list_view,
    template_lesson_detail_json,
)

urlpatterns = [
    path("", real_lesson_list_view, name="real_lesson_home"),  # по умолчанию: /schedule/
    path("template-week/", template_week_view, name="template_week"),
    path("real-lesson/create/", real_lesson_create_view, name="real_lesson_create"),
    path("real-lessons/", real_lesson_list_view, name="real_lesson_list"),
    path("api/template-lesson/<int:pk>/", template_lesson_detail_json, name="template_lesson_detail_json"),
]
