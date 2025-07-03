from django import forms
from .models import TemplateLesson, TeacherAvailability
from users.models import UserSubject, UserGrade

class TemplateLessonForm(forms.ModelForm):
    class Meta:
        model = TemplateLesson
        fields = ['template_week', 'grade', 'subject', 'teacher', 'day_of_week', 'start_time', 'duration_minutes']
        widgets = {
            'start_time': forms.TimeInput(format='%H:%M', attrs={
                'type': 'time',
                'step': 300,  # шаг в 5 минут
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        teacher = cleaned_data.get('teacher')
        subject = cleaned_data.get('subject')
        grade = cleaned_data.get('grade')
        day = cleaned_data.get('day_of_week')
        start = cleaned_data.get('start_time')
        duration = cleaned_data.get('duration_minutes')

        if not teacher or not subject or not grade or day is None or not start or not duration:
            return cleaned_data  # Пропускаем, если что-то пустое

        # Проверка — предмет
        if not UserSubject.objects.filter(teacher=teacher, subject=subject).exists():
            raise forms.ValidationError(f"{teacher} не преподаёт предмет «{subject}».")

        # Проверка — класс
        if not UserGrade.objects.filter(teacher=teacher, grade=grade).exists():
            raise forms.ValidationError(f"{teacher} не работает с классом «{grade}».")

        # Проверка — занятость по времени
        from datetime import timedelta, datetime

        start_dt = datetime.combine(datetime.today(), start)
        end_dt = start_dt + timedelta(minutes=duration)
        end = end_dt.time()

        if not TeacherAvailability.objects.filter(
            teacher=teacher,
            day_of_week=day,
            start_time__lte=start,
            end_time__gte=end
        ).exists():
            raise forms.ValidationError(f"{teacher} недоступен в это время: {start}–{end}.")

        return cleaned_data

    def clean_duration_minutes(self):
        duration = self.cleaned_data.get('duration_minutes')
        if duration < 15 or duration > 120:
            raise forms.ValidationError("Длительность урока должна быть от 15 до 120 минут.")
        return duration
