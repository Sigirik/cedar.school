"""
Сериализатор активного черновика.
"""

from rest_framework import serializers
from .models import TemplateWeekDraft
from schedule.validators.schedule_rules import check_collisions  # <— импорт

class TemplateWeekDraftSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    collisions = serializers.SerializerMethodField()  # <— новое поле

    class Meta:
        model = TemplateWeekDraft
        fields = "__all__"  # collisions попадёт автоматически

    def get_collisions(self, obj):
        lessons = (obj.data or {}).get("lessons", [])
        # lessons — в формате твоего черновика: id, day_of_week, start_time, duration_minutes, teacher, grade, subject
        return check_collisions(lessons)
