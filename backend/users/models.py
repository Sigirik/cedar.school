# backend/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Админ"
        DIRECTOR = "DIRECTOR", "Директор"
        HEAD_TEACHER = "HEAD_TEACHER", "Завуч"
        METHODIST = "METHODIST", "Методист"
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

class ParentChild(models.Model):
    """
    Явная связь Родитель → Ребёнок (Student).
    Не меняем модель User; используем отдельную таблицу связей.
    """
    parent = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="children_links",
        help_text="Родитель (роль: PARENT)",
    )
    child = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="parent_links",
        help_text="Ребёнок/ученик (роль: STUDENT)",
    )
    is_active = models.BooleanField(default=True)
    relation = models.CharField(
        max_length=32,
        blank=True,
        help_text="Тип связи (мама/папа/опекун и т.п., опционально)",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("parent", "child"),)
        indexes = [
            models.Index(fields=["parent", "is_active"]),
            models.Index(fields=["child", "is_active"]),
        ]
        verbose_name = "Связь родитель-ребёнок"
        verbose_name_plural = "Связи родитель-ребёнок"

    def clean(self):
        # Мягкая валидация ролей (без DB CHECK)
        if self.parent and getattr(self.parent, "role", None) != User.Role.PARENT:
            raise ValidationError("parent.role должен быть PARENT")
        if self.child and getattr(self.child, "role", None) != User.Role.STUDENT:
            raise ValidationError("child.role должен быть STUDENT")

    def __str__(self):
        state = "active" if self.is_active else "inactive"
        return f"{self.parent_id} → {self.child_id} ({state})"