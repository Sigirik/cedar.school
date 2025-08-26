from django.db import models
from django.conf import settings
from schedule.core.models import Subject, Grade
from schedule.template.models import TemplateLesson

DAY_CHOICES = (
    (0, "Понедельник"),
    (1, "Вторник"),
    (2, "Среда"),
    (3, "Четверг"),
    (4, "Пятница"),
    (5, "Суббота"),
    (6, "Воскресенье"),
)

class RealLesson(models.Model):
    date = models.DateField()
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "TEACHER"}
    )
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)
    start_time = models.TimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=45)
    topic = models.CharField(max_length=255, blank=True)
    theme_from_ktp = models.CharField(max_length=255, blank=True)
    template_lesson = models.ForeignKey(TemplateLesson, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["date", "start_time"]

    def __str__(self):
        return f"{self.date} {self.grade} — {self.subject}"

    @property
    def end_time(self):
        from datetime import timedelta, datetime
        start = datetime.combine(self.date, self.start_time)
        return (start + timedelta(minutes=self.duration_minutes)).time()
