# backend/schedule/real_schedule/urls.py
from django.urls import path
from schedule.real_schedule.views import (
    GenerateRealScheduleView, ConductLessonView,
    RoomGetOrCreateView, RoomEndView,
)
from schedule.real_schedule.views_my import MyScheduleView

urlpatterns = [
    path("my/", MyScheduleView.as_view()),

    path("generate/", GenerateRealScheduleView.as_view()),
    path("lessons/<int:pk>/conduct/", ConductLessonView.as_view()),
    path("rooms/get-or-create/", RoomGetOrCreateView.as_view()),
    path("rooms/<int:pk>/end/", RoomEndView.as_view()),
]
