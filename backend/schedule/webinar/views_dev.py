from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
import os

class DevMakeDummyRecordingView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if not settings.DEBUG:
            return Response({"detail": "Not allowed in production"}, status=403)

        secret = request.headers.get("X-Recording-Secret", "")
        configured = getattr(settings, "RECORDING_WEBHOOK_SECRET", None)
        if configured and secret != configured:
            return Response({"detail": "Forbidden"}, status=403)

        path = request.data.get("path") or "/tmp/dummy.mp4"
        size_mb = int(request.data.get("size_mb") or 1)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(b"\0" * (size_mb * 1024 * 1024))
        return Response({"file_path": path, "size_bytes": size_mb * 1024 * 1024}, status=201)
