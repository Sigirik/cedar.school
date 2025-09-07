from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timezone as dt_timezone
# core / ktp
from schedule.core.models import Subject, Grade, LessonType
from schedule.ktp.models import KTPEntry


class RealLesson(models.Model):
    class Source(models.TextChoices):
        TEMPLATE = "TEMPLATE"
        MANUAL   = "MANUAL"
        IMPORT   = "IMPORT"

    subject  = models.ForeignKey(Subject, on_delete=models.PROTECT)
    grade    = models.ForeignKey(Grade, on_delete=models.PROTECT)
    teacher  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    start    = models.DateTimeField(db_index=True)  # UTC
    duration_minutes = models.PositiveIntegerField()

    lesson_type = models.ForeignKey(LessonType, on_delete=models.PROTECT)
    topic_order = models.PositiveIntegerField(null=True, blank=True)
    topic_title = models.CharField(max_length=255, null=True, blank=True)
    ktp_entry  = models.ForeignKey(KTPEntry, null=True, blank=True, on_delete=models.SET_NULL)

    source = models.CharField(max_length=16, choices=Source.choices, default=Source.TEMPLATE)
    template_week_id   = models.IntegerField(null=True, blank=True)
    template_lesson_id = models.IntegerField(null=True, blank=True)
    generation_batch_id = models.UUIDField(null=True, blank=True, db_index=True)
    version = models.PositiveIntegerField(default=1)

    conducted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["grade", "start"]),
            models.Index(fields=["teacher", "start"]),
            models.Index(fields=["source", "start"]),
        ]

    def __str__(self):
        return f"{self.subject} {self.grade} {self.start.astimezone(dt_timezone.utc)}"

class Room(models.Model):
    class Provider(models.TextChoices):
        JITSI = "JITSI"
        BBB   = "BBB"
        ZOOM  = "ZOOM"

    lesson = models.OneToOneField(RealLesson, on_delete=models.CASCADE, related_name="room")
    provider = models.CharField(max_length=16, choices=Provider.choices)
    join_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    started_at = models.DateTimeField(null=True, blank=True)
    ended_at   = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.provider} room for lesson {self.lesson_id}"


class LessonStudent(models.Model):
    class Status(models.TextChoices):
        PRESENT = "+",    "Присутствовал"
        ABSENT  = "-",    "Отсутствовал"
        LATE    = "late", "Опоздал"

    lesson   = models.ForeignKey("real_schedule.RealLesson", on_delete=models.CASCADE, related_name="lesson_students")
    student  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_entries")

    status        = models.CharField(max_length=4, choices=Status.choices, null=True, blank=True)
    late_minutes  = models.PositiveSmallIntegerField(null=True, blank=True)  # для status=late
    mark          = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,
                                        validators=[MinValueValidator(0), MaxValueValidator(10)])  # пример шкалы 0–10

    class Meta:
        unique_together = ("lesson", "student")
        indexes = [models.Index(fields=["lesson", "student"])]

    def clean(self):
        # late → нужно указать минуты; не late → minutes сбрасываем
        from django.core.exceptions import ValidationError
        if self.status == self.Status.LATE and (self.late_minutes is None):
            raise ValidationError({"late_minutes": "Укажите количество минут опоздания."})
        if self.status != self.Status.LATE:
            self.late_minutes = None