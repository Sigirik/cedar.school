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
    middle_name = models.CharField("Отчество", max_length=150, blank=True)
    individual_subjects_enabled = models.BooleanField(
        "Индивидуальный выбор предметов",
        default=False,
        help_text="Включить для ученика возможность индивидуального выбора предметов, иначе — все предметы наследуются от класса"
    )

    def __str__(self):
        return f"{self.username} ({self.role})"

class RoleRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Ожидает'
        APPROVED = 'APPROVED', 'Подтверждено'
        REJECTED = 'REJECTED', 'Отклонено'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    requested_role = models.CharField(max_length=20, choices=User.Role.choices)
    full_name = models.CharField(max_length=255)
    additional_info = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    def __str__(self):
        return f"{self.user.username} → {self.requested_role} ({self.status})"
