"""
Модуль ktp/serializers.py:
Сериализаторы календарно-тематических планов (КТП).
"""

from rest_framework import serializers
from .models import KTPTemplate, KTPSection, KTPEntry
from schedule.core.serializers import SubjectSerializer, GradeSerializer
from schedule.template.serializers import TemplateLessonSerializer

class KTPEntrySerializer(serializers.ModelSerializer):
    section = serializers.PrimaryKeyRelatedField(queryset=KTPSection.objects.all())

    class Meta:
        model = KTPEntry
        fields = '__all__'
        extra_kwargs = {
            'title': {'required': False, 'allow_blank': True},
            'planned_date': {'required': False, 'allow_null': True},
            'actual_date': {'required': False, 'allow_null': True},
            'objectives': {'required': False, 'allow_blank': True},
            'tasks': {'required': False, 'allow_blank': True},
            'homework': {'required': False, 'allow_blank': True},
            'materials': {'required': False, 'allow_blank': True},
            'planned_outcomes': {'required': False, 'allow_blank': True},
            'motivation': {'required': False, 'allow_blank': True},
            'template_lesson': {'required': False, 'allow_null': True},
        }

    def create(self, validated_data):
        section = validated_data["section"]

        # Автоматически выставить номер урока, если не передан
        if "lesson_number" not in validated_data:
            last_lesson = KTPEntry.objects.filter(section=section).order_by("-lesson_number").first()
            validated_data["lesson_number"] = last_lesson.lesson_number + 1 if last_lesson else 1

        # Автоматически выставить порядок
        if "order" not in validated_data:
            last_entry = KTPEntry.objects.filter(section=section).order_by("-order").first()
            validated_data["order"] = last_entry.order + 1 if last_entry else 1

        return super().create(validated_data)

class KTPSectionSerializer(serializers.ModelSerializer):
    entries = KTPEntrySerializer(many=True, read_only=True)

    class Meta:
        model = KTPSection
        fields = '__all__'

class KTPTemplateSerializer(serializers.ModelSerializer):
    sections = KTPSectionSerializer(many=True, read_only=True)

    class Meta:
        model = KTPTemplate
        fields = '__all__'