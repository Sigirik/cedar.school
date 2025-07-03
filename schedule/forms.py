from django import forms
from .models import TemplateLesson, TeacherAvailability
from users.models import UserSubject, UserGrade

class TemplateLessonForm(forms.ModelForm):
    class Meta:
        model = TemplateLesson
        fields = ['template_week', 'grade', 'subject', 'teacher', 'day_of_week', 'start_time', 'end_time']

    def clean(self):
        cleaned_data = super().clean()
        teacher = cleaned_data.get('teacher')
        subject = cleaned_data.get('subject')
        grade = cleaned_data.get('grade')
        day = cleaned_data.get('day_of_week')
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')

        if not teacher or not subject or not grade or not day or not start or not end:
            return cleaned_data  # Пропускаем пустые поля

        # ❌ Предмет
        if not UserSubject.objects.filter(teacher=teacher, subject=subject).exists():
            raise forms.ValidationError(f"{teacher} не преподаёт предмет «{subject}».")

        # ❌ Класс
        if not UserGrade.objects.filter(teacher=teacher, grade=grade).exists():
            raise forms.ValidationError(f"{teacher} не работает с классом «{grade}».")

        # ❌ Время
        if not TeacherAvailability.objects.filter(
            teacher=teacher,
            day_of_week=day,
            start_time__lte=start,
            end_time__gte=end
        ).exists():
            raise forms.ValidationError(f"{teacher} недоступен в это время: {start}–{end}.")

        return cleaned_data
