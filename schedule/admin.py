from django.contrib import admin
from .models import (
    AcademicYear,
    Grade,
    Subject,
    WeeklyNorm,
    TeacherAvailability,
    TemplateWeek,
    TemplateLesson,
    RealLesson,
)
from .forms import TemplateLessonForm


@admin.register(TemplateLesson)
class TemplateLessonAdmin(admin.ModelAdmin):
    form = TemplateLessonForm
    list_display = ("template_week", "grade", "subject", "teacher", "day_of_week", "start_time", "duration_minutes")
    list_filter = ("template_week", "day_of_week", "teacher", "grade", "subject")
    search_fields = ("template_week__name", "grade__name", "teacher__username", "subject__name")

    def save_model(self, request, obj, form, change):
        # Валидируем данные перед сохранением
        obj.full_clean()
        super().save_model(request, obj, form, change)


admin.site.register(AcademicYear)
admin.site.register(Grade)
admin.site.register(Subject)
admin.site.register(WeeklyNorm)
admin.site.register(TeacherAvailability)
admin.site.register(TemplateWeek)
admin.site.register(RealLesson)