from django.contrib import admin
from .models import RealLesson
from .forms import RealLessonForm

@admin.register(RealLesson)
class RealLessonAdmin(admin.ModelAdmin):
    list_display = ('date', 'grade', 'subject', 'teacher', 'start_time', 'duration_minutes', 'topic')
    list_filter = ('date', 'grade', 'subject', 'teacher')
    search_fields = ('topic',)
