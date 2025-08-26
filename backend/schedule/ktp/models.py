"""
Модуль ktp/models.py:
Модели для календарно-тематических планов (КТП).
"""

from django.db import models
from schedule.core.models import Subject, Grade, AcademicYear
from schedule.template.models import TemplateWeek, TemplateLesson

# Шаблон КТП — объединяет тему, класс и учебный год.
# Пример: "КТП по математике 5А 2024–2025"
class KTPTemplate(models.Model):
    last_template_week_used = models.ForeignKey(
        TemplateWeek, null=True, blank=True, on_delete=models.SET_NULL,
        help_text="Шаблон недели, по которому последний раз были распределены даты"
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='ktp_templates')
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='ktp_templates')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)  # Например: "КТП по математике 5А"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Раздел внутри шаблона КТП.
# Пример: "Тема 1: Натуральные числа", "Раздел 2: Геометрия"
class KTPSection(models.Model):
    ktp_template = models.ForeignKey(KTPTemplate, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField()
    hours = models.PositiveIntegerField(default=0)  # Кол-во часов в разделе

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


# Конкретная запись КТП — одно занятие/урок.
# Пример: "Урок 1: Сложение натуральных чисел"
class KTPEntry(models.Model):
    LESSON_TYPE_CHOICES = [
        ('lesson', 'Урок'),
        ('course', 'Курс'),
    ]

    section = models.ForeignKey(KTPSection, on_delete=models.CASCADE, related_name='entries')
    lesson_number = models.PositiveIntegerField(default=1)
    type = models.CharField(max_length=10, choices=LESSON_TYPE_CHOICES, default='lesson')
    planned_date = models.DateField(blank=True, null=True)
    actual_date = models.DateField(blank=True, null=True)
    title = models.CharField(max_length=255)
    objectives = models.TextField(blank=True, null=True)
    tasks = models.TextField(blank=True, null=True)
    homework = models.TextField(blank=True, null=True)
    materials = models.TextField(blank=True, null=True)
    planned_outcomes = models.TextField(blank=True, null=True)
    motivation = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField()
    template_lesson = models.ForeignKey(
        TemplateLesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title