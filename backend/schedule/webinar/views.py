# backend/schedule/webinar/views.py
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny


from schedule.webinar.services.recordings import (
    recording_uploaded_from_jaas,
    recording_uploaded_from_jibri,
)
from schedule.real_schedule.models import Room

class JaasRecordingWebhookView(APIView):
    """
    JaaS webhook payload example:
    {
      "room_id": 123,
      "preAuthenticatedLink": "https://.../download?sig=...",
      "fileExt": "mp4"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        secret = request.headers.get("X-Recording-Secret", "")
        configured = getattr(settings, "RECORDING_WEBHOOK_SECRET", None)
        if configured and secret != configured:
            return HttpResponse(status=403)

        room_id = request.data.get("room_id")
        link = request.data.get("preAuthenticatedLink")
        ext = request.data.get("fileExt", "mp4")

        if not (room_id and link):
            return JsonResponse({"detail": "room_id and preAuthenticatedLink are required"}, status=400)

        try:
            room = recording_uploaded_from_jaas(int(room_id), link, file_ext=ext)
        except Room.DoesNotExist:
            return JsonResponse({"detail": "Room not found"}, status=404)
        except Exception as e:
            return JsonResponse({"detail": str(e)}, status=500)

        return JsonResponse({"status": room.recording_status, "file_url": room.recording_file_url}, status=200)

class RoomRecordingUploadedView(APIView):
    """
    Internal endpoint for Jibri finalize script.
    Payload:
    {
      "file_path": "/var/jibri/recordings/lesson-456.mp4",
      "file_ext": "mp4"  # optional
    }
    """
    permission_classes = [AllowAny]

    def post(self, request, room_id: int, *args, **kwargs):
        secret = request.headers.get("X-Recording-Secret", "")
        configured = getattr(settings, "RECORDING_WEBHOOK_SECRET", None)
        if configured and secret != configured:
            return HttpResponse(status=403)

        file_path = request.data.get("file_path")
        file_ext = request.data.get("file_ext")

        if not file_path:
            return JsonResponse({"detail": "file_path is required"}, status=400)

        try:
            room = recording_uploaded_from_jibri(int(room_id), file_path, file_ext=file_ext)
        except Room.DoesNotExist:
            return JsonResponse({"detail": "Room not found"}, status=404)
        except Exception as e:
            return JsonResponse({"detail": str(e)}, status=500)

        return JsonResponse({"status": room.recording_status, "file_url": room.recording_file_url}, status=200)
