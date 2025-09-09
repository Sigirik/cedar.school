from django.contrib import admin
from schedule.real_schedule.models import RealLesson, Room
from .forms import RealLessonForm
from .models import Room

@admin.register(RealLesson)
class RealLessonAdmin(admin.ModelAdmin):
    form = RealLessonForm
    list_display = ("id", "subject", "grade", "teacher", "start", "duration_minutes",
                    "lesson_type", "source", "topic_title", "is_open", "conducted_at")
    list_filter = ("source", "lesson_type", "grade", "subject", "teacher", "is_open")
    search_fields = ("subject__name", "grade__name", "teacher__username", "topic_title")
    readonly_fields = ("generation_batch_id",)
    ordering = ("-start",)

    # Важно: не фильтруем queryset по пользователю — иначе у админа может быть 404
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs  # без дополнительных фильтров

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "id", "type", "lesson",
        "jitsi_env", "jitsi_domain", "jitsi_room",
        "status", "is_open",
        "scheduled_start", "scheduled_end",
        "recording_status",
    )
    list_filter = ("type", "status", "is_open", "jitsi_env", "recording_status")
    search_fields = ("jitsi_room", "lesson__id")
    readonly_fields = (
        "created_at", "started_at", "ended_at",
        "recording_started_at", "recording_ended_at",
        "recording_status", "recording_file_url",
    )
    fieldsets = (
        ("Базовое", {"fields": ("type", "lesson", "is_open", "public_slug", "status")}),
        ("Время", {"fields": ("scheduled_start", "scheduled_end", "started_at", "ended_at")}),
        ("Jitsi", {"fields": ("jitsi_env", "jitsi_domain", "jitsi_room", "join_url")}),
        ("Запись", {"fields": (
            "recording_status", "recording_file_url",
            "recording_started_at", "recording_ended_at",
            "recording_duration_secs", "recording_storage", "recording_meta",
        )}),
        ("Служебное", {"fields": ("created_at",)}),
    )
