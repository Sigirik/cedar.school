# schedule/core/admin.py
from django.contrib import admin
from schedule.core.models import AcademicYear, Grade, Subject, WeeklyNorm, TeacherAvailability, LessonType
from .models import TeacherSubject, TeacherGrade, GradeSubject, StudentSubject

admin.site.register(AcademicYear)
admin.site.register(Grade)
admin.site.register(Subject)
admin.site.register(WeeklyNorm)
admin.site.register(LessonType)
admin.site.register(TeacherSubject)
admin.site.register(TeacherGrade)
admin.site.register(GradeSubject)
admin.site.register(StudentSubject)
admin.site.register(TeacherAvailability)



