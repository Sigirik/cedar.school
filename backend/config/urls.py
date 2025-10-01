"""
URL configuration for config project.
"""
from django.http import JsonResponse
import os, datetime
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from schedule.webinar.views_dev import DevMakeDummyRecordingView

def health(_request):
    return JsonResponse({"status": "ok"}, status=200)

def version(_request):
    return JsonResponse({"version": os.environ.get("GIT_SHA", "unknown")})

def time_view(_request):
    from zoneinfo import ZoneInfo
    tzname = os.getenv("TIME_ZONE", "UTC")
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_local = datetime.datetime.now(ZoneInfo(tzname))
    return JsonResponse({
        "utc": now_utc.isoformat(),
        "local": now_local.isoformat(),
        "tz": tzname
    })

urlpatterns = [
    path("health", health),
    path("version", version),
    path("time", time_view),
    # Admin
    path("admin/", admin.site.urls),

    # DRF auth (optional)
    path("api-auth/", include("rest_framework.urls")),

    # Business modules
    path("api/core/", include("schedule.core.urls")),
    path("api/template/", include("schedule.template.urls")),
    path("api/draft/", include(("schedule.draft.urls", "draft"), namespace="draft")),
    path("api/ktp/", include("schedule.ktp.urls")),
    path("api/real_schedule/", include("schedule.real_schedule.urls")),
    path("api/reference/", include("schedule.reference.urls")),

    # Webinar recordings (webhooks & finalize)
    path("api/rooms/", include("schedule.webinar.urls_rooms")),  # все операции с комнатами
    path("api/", include("schedule.webinar.urls")),  # вебхуки/финализация записей
    path("recordings/make-dummy/", DevMakeDummyRecordingView.as_view(), name="dev-make-dummy"),

    # Users & roles (routers inside)
    path("api/", include("users.urls")),

    # Djoser + JWT
    path("api/auth/", include("djoser.urls")),
    path("api/auth/", include("djoser.urls.jwt")),

    # Classic Django auth (optional)
    path("accounts/", include("django.contrib.auth.urls")),

    # Custom registration URLs if you have them
    path("api/auth/", include("users.registration_urls")),
]

# In DEV: serve /media/recordings/* directly from RECORDING_LOCAL_DIR
if getattr(settings, "SERVE_RECORDINGS_VIA_DJANGO", False):
    urlpatterns += static("/media/recordings/", document_root=settings.RECORDING_LOCAL_DIR)

if settings.DEBUG:
    urlpatterns += [ path("api/dev/", include("schedule.webinar.urls_dev")) ]
