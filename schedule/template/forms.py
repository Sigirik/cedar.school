from django import forms
from schedule.core.models import TeacherAvailability, TeacherSubject, TeacherGrade
from .models import TemplateLesson
from django.core.exceptions import ValidationError

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
        if not TeacherSubject.objects.filter(teacher=teacher, subject=subject).exists():
            raise forms.ValidationError(f"{teacher} не преподаёт предмет «{subject}».")

        # Проверка — класс
        if not TeacherGrade.objects.filter(teacher=teacher, grade=grade).exists():
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

        # Проверка — занят ли класс в это время другим уроком
        from .models import TemplateLesson
        overlapping_lessons = TemplateLesson.objects.filter(
            grade=grade,
            day_of_week=day
        ).exclude(pk=self.instance.pk)

        for lesson in overlapping_lessons:
            existing_start = datetime.combine(datetime.today(), lesson.start_time)
            existing_end = existing_start + timedelta(minutes=lesson.duration_minutes)
            new_start = datetime.combine(datetime.today(), start)
            new_end = new_start + timedelta(minutes=duration)

            if not (new_end <= existing_start or new_start >= existing_end):
                raise forms.ValidationError(
                    f"Класс {grade} уже занят в это время: {lesson.subject} с {lesson.teacher} ({lesson.start_time}–{lesson.end_time})"
                )

        return cleaned_data

    def clean_duration_minutes(self):
        duration = self.cleaned_data.get('duration_minutes')
        if duration < 15 or duration > 120:
            raise forms.ValidationError("Длительность урока должна быть от 15 до 120 минут.")
        return duration