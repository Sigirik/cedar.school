from django.contrib.auth.models import AbstractUser
from django.db import models

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

    def __str__(self):
        return f"{self.username} ({self.role})"