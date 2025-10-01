"""
Модуль template/models.py:
Содержит модели для хранения шаблонов недель и уроков.
"""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from schedule.core.models import Grade, Subject, AcademicYear, LessonType, TeacherAvailability, TeacherSubject, TeacherGrade  # импортируем из core

# Шаблон недели (например, "Неделя №1") — основа для генерации расписания
class TemplateWeek(models.Model):
    name = models.CharField(max_length=100, help_text="Название шаблона (например: Неделя №1)")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, default="")

    def __str__(self):
        return self.name

WEEKDAYS = [
    "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"
]
DAY_CHOICES = [(i, WEEKDAYS[i]) for i in range(7)]

class TemplateLesson(models.Model):
    template_week = models.ForeignKey('TemplateWeek', on_delete=models.CASCADE, related_name="lessons")
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "TEACHER"}
    )
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=45)
    type = models.ForeignKey(
        LessonType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='lessons'
    )

    class Meta:
        ordering = ["day_of_week", "start_time"]

    def __str__(self):
        weekday = WEEKDAYS[self.day_of_week] if self.day_of_week < len(WEEKDAYS) else self.day_of_week
        return f"{self.template_week} | {self.grade} | {weekday} {self.start_time} — {self.subject}"

    @property
    def lesson_type(self):
        """Совместимость со старыми вызовами: .lesson_type == .type"""
        return self.type

    def clean(self):
        user = self.teacher
        is_superuser = getattr(user, "is_superuser", False)
        role = getattr(user, "role", None)

        # Проверка: входит ли день/время в доступное расписание
        available = TeacherAvailability.objects.filter(
            teacher=user,
            day_of_week=self.day_of_week,
            start_time__lte=self.start_time,
            end_time__gte=self.get_end_time()
        ).exists()

        if not available:
            if is_superuser or role in ["DIRECTOR", "HEAD_TEACHER"]:
                print(f"⚠️ Предупреждение: {user} вне времени занятости")
            else:
                raise ValidationError("Учитель недоступен в это время")

        # Проверка: преподаватель должен быть привязан к предмету
        if not TeacherSubject.objects.filter(teacher=self.teacher, subject=self.subject).exists():
            if is_superuser or role in ["DIRECTOR", "HEAD_TEACHER"]:
                print(f"⚠️ Предупреждение: {user} не привязан к предмету {self.subject}")
            else:
                raise ValidationError("Учитель не привязан к данному предмету")

        # Проверка: преподаватель должен быть привязан к классу
        if not TeacherGrade.objects.filter(teacher=self.teacher, grade=self.grade).exists():
            if is_superuser or role in ["DIRECTOR", "HEAD_TEACHER"]:
                print(f"⚠️ Предупреждение: {user} не привязан к классу {self.grade}")
            else:
                raise ValidationError("Учитель не привязан к данному классу")

    def get_end_time(self):
        from datetime import timedelta, datetime
        start = datetime.combine(datetime.today(), self.start_time)
        return (start + timedelta(minutes=self.duration_minutes)).time()

class ActiveTemplateWeek(models.Model):
    template = models.OneToOneField(TemplateWeek, on_delete=models.CASCADE)
    activated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Активная неделя: {self.template.name}"

