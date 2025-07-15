from django import forms
from .models import TemplateLesson, TeacherAvailability, RealLesson
from users.models import UserSubject, UserGrade
from datetime import timedelta, datetime
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
