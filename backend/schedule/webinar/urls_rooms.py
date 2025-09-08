# backend/schedule/webinar/urls_rooms.py
from django.urls import path
from .views_rooms import (
    RoomByLessonView, RoomRetrieveView,
    MeetingCreateView, RoomCloseView, RecordingMetaView
)

urlpatterns = [
    path("by-lesson/<int:lesson_id>/", RoomByLessonView.as_view(), name="room-by-lesson"),
    path("<int:room_id>/", RoomRetrieveView.as_view(), name="room-retrieve"),
    path("meeting/", MeetingCreateView.as_view(), name="room-meeting-create"),
    path("<int:room_id>/close/", RoomCloseView.as_view(), name="room-close"),
    path("<int:room_id>/recording/", RecordingMetaView.as_view(), name="room-recording"),
]
