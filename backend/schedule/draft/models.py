"""
Модуль draft/models.py:
Модели для хранения черновиков шаблонных недель и их уроков.
Хранит только один активный черновик недели.
"""

from django.db import models
from django.conf import settings
from schedule.template.models import TemplateWeek

class TemplateWeekDraft(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # Теперь только OneToOneField
        on_delete=models.CASCADE
    )
    base_week = models.ForeignKey(TemplateWeek, on_delete=models.CASCADE, null=True, blank=True)
    data = models.JSONField(default=dict)
    change_history = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Draft by {self.user} for {self.base_week.name if self.base_week else 'empty'}"
