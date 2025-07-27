from django import forms
from .models import RealLesson
from datetime import timedelta, datetime
from django.core.exceptions import ValidationError



class RealLessonForm(forms.ModelForm):
    class Meta:
        model = RealLesson
        fields = [
            'date',
            'subject',
            'teacher',
            'grade',
            'start_time',
            'duration_minutes',
            'topic',
            'template_lesson'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        teacher = cleaned_data.get('teacher')
        grade = cleaned_data.get('grade')
        start = cleaned_data.get('start_time')
        duration = cleaned_data.get('duration_minutes')
        date = cleaned_data.get('date')
        template = cleaned_data.get('template_lesson')

        if not all([teacher, grade, start, duration, date]):
            # дата обязательна перед выбором шаблона
            if template and not date:
                raise ValidationError("Сначала выберите дату, чтобы выбрать шаблон урока.")
            return cleaned_data

        # Автоматическое определение дня недели
        cleaned_data['day_of_week'] = date.weekday()

        # Проверка соответствия шаблона дню недели
        if template:
            if template.day_of_week != date.weekday():
                raise ValidationError(
                    f"Шаблон «{template}» предназначен для {template.get_day_of_week_display()}, "
                    f"а выбрана дата — {date.strftime('%A')}."
                )

        new_start_dt = datetime.combine(date, start)
        new_end_dt = new_start_dt + timedelta(minutes=duration)

        # Проверка пересечения по классу
        overlapping_class = RealLesson.objects.filter(
            date=date,
            grade=grade
        ).exclude(pk=self.instance.pk)
        for lesson in overlapping_class:
            existing_start = datetime.combine(lesson.date, lesson.start_time)
            existing_end = existing_start + timedelta(minutes=lesson.duration_minutes)
            if new_start_dt < existing_end and new_end_dt > existing_start:
                raise ValidationError(
                    f"У класса {grade} уже есть урок в это время: {lesson.subject} ({lesson.start_time}–{lesson.end_time})")

        # Проверка пересечения по учителю
        overlapping_teacher = RealLesson.objects.filter(
            date=date,
            teacher=teacher
        ).exclude(pk=self.instance.pk)
        for lesson in overlapping_teacher:
            existing_start = datetime.combine(lesson.date, lesson.start_time)
            existing_end = existing_start + timedelta(minutes=lesson.duration_minutes)
            if new_start_dt < existing_end and new_end_dt > existing_start:
                raise ValidationError(
                    f"У учителя {teacher} уже есть урок в это время: {lesson.subject} ({lesson.start_time}–{lesson.end_time})")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        instance.day_of_week = self.cleaned_data['day_of_week']

        # Автозаполнение из шаблона
        if instance.template_lesson:
            instance.subject = instance.template_lesson.subject
            instance.teacher = instance.template_lesson.teacher
            instance.grade = instance.template_lesson.grade
            instance.start_time = instance.template_lesson.start_time
            instance.duration_minutes = instance.template_lesson.duration_minutes

        # Тема по умолчанию
        if not instance.topic:
            instance.topic = "Тема не задана"

        if commit:
            instance.save()
        return instance
