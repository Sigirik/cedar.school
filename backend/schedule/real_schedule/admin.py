from django.contrib import admin
from schedule.real_schedule.models import RealLesson, Room
from .forms import RealLessonForm

@admin.register(RealLesson)
class RealLessonAdmin(admin.ModelAdmin):
    form = RealLessonForm
    list_display = ("id", "subject", "grade", "teacher", "start", "duration_minutes",
                    "lesson_type", "source", "topic_title", "conducted_at")
    list_filter = ("source", "lesson_type", "grade", "teacher")
    search_fields = ("subject__name", "grade__name", "teacher__username", "topic_title")
    readonly_fields = ("generation_batch_id",)
    ordering = ("-start",)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("id", "lesson", "provider", "created_at", "started_at", "ended_at")
    list_filter = ("provider",)
    search_fields = ("lesson__subject__name", "lesson__grade__name")
