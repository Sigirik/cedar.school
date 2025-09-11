# backend/schedule/real_schedule/urls.py
from django.urls import path
from schedule.real_schedule.views import (
    GenerateRealScheduleView, ConductLessonView,
    RoomGetOrCreateView, RoomEndView, LessonDetailView,
)
from schedule.real_schedule.views_my import MyScheduleView, RealLessonsListView, ViewAsScheduleView

urlpatterns = [
    path("my/", MyScheduleView.as_view()),

    path("generate/", GenerateRealScheduleView.as_view()),
    path("rooms/get-or-create/", RoomGetOrCreateView.as_view()),
    path("rooms/<int:pk>/end/", RoomEndView.as_view()),
    path("lessons/<int:pk>/conduct/", ConductLessonView.as_view()),
    path("lessons/<int:id>/", LessonDetailView.as_view(), name="lesson-detail"),
    path("lessons/", RealLessonsListView.as_view()),
    path("view_as/<int:user_id>/", ViewAsScheduleView.as_view())
]
