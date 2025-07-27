"""
Модуль ktp/serializers.py:
Сериализаторы календарно-тематических планов (КТП).
"""

from rest_framework import serializers
from .models import KTPTemplate, KTPSection, KTPEntry
from schedule.core.serializers import SubjectSerializer, GradeSerializer
from schedule.template.serializers import TemplateLessonSerializer

class KTPEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = KTPEntry
        fields = '__all__'

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