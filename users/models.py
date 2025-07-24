from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from schedule.models import Grade, Subject

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Админ"
        DIRECTOR = "DIRECTOR", "Директор"
        HEAD_TEACHER = "HEAD_TEACHER", "Завуч"
        AUDITOR = "AUDITOR", "Аудитор"
        TEACHER = "TEACHER", "Учитель"
        PARENT = "PARENT", "Родитель"
        STUDENT = "STUDENT", "Ученик"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    middle_name = models.CharField("Отчество", max_length=150, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

class UserSubject(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'TEACHER'})
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.teacher} — {self.subject}"

class UserGrade(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'TEACHER'})
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.teacher} — {self.grade}"