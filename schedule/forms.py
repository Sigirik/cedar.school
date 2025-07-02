from django import forms
from .models import TemplateLesson

class TemplateLessonForm(forms.ModelForm):
    class Meta:
        model = TemplateLesson
        fields = ['template_week', 'grade', 'subject', 'teacher', 'day_of_week', 'start_time', 'end_time']