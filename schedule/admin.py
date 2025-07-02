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

admin.site.register(AcademicYear)
admin.site.register(Grade)
admin.site.register(Subject)
admin.site.register(WeeklyNorm)
admin.site.register(TeacherAvailability)
admin.site.register(TemplateWeek)
admin.site.register(TemplateLesson)
admin.site.register(RealLesson)