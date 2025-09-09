# backend/schedule/webinar/urls.py
from django.urls import path
from .views import JaasRecordingWebhookView, RoomRecordingUploadedView

urlpatterns = [
    path("webhooks/jaas/recording/", JaasRecordingWebhookView.as_view(), name="jaas-recording-webhook"),
    path("rooms/<int:room_id>/recording/uploaded/", RoomRecordingUploadedView.as_view(), name="room-recording-uploaded"),
]
