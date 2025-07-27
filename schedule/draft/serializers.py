"""
Сериализатор активного черновика.
"""

from rest_framework import serializers
from .models import TemplateWeekDraft

class TemplateWeekDraftSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TemplateWeekDraft
        fields = "__all__"
