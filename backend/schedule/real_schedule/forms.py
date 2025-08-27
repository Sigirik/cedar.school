from django import forms
from django.utils import timezone
import datetime as dt
from schedule.real_schedule.models import RealLesson

class RealLessonForm(forms.ModelForm):
    # Доп. удобство в админке: раздельные поля даты/времени (не из модели)
    date = forms.DateField(required=False, widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}))
    start_time = forms.TimeField(required=False, widget=forms.TimeInput(format="%H:%M", attrs={"type": "time"}))

    class Meta:
        model = RealLesson
        # ВНИМАНИЕ: тут только ПОЛЯ МОДЕЛИ (никаких date/start_time/template_lesson/topic)
        fields = [
            "subject", "grade", "teacher",
            "start", "duration_minutes",
            "lesson_type", "topic_title", "ktp_entry",
            "source", "template_week_id", "template_lesson_id",
            "version", "conducted_at",
        ]
        widgets = {
            "start": forms.DateTimeInput(format="%Y-%m-%d %H:%M", attrs={"type": "datetime-local"})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Инициализируем вспомогательные поля из start
        if self.instance and self.instance.start:
            local = self.instance.start.astimezone(timezone.utc)  # у тебя UTC — оставим так
            self.fields["date"].initial = local.date()
            self.fields["start_time"].initial = local.time().replace(microsecond=0)

    def clean(self):
        cleaned = super().clean()
        date = cleaned.get("date")
        t = cleaned.get("start_time")
        start = cleaned.get("start")
        # Если указали раздельно дату/время — склеим в start
        if date and t:
            cleaned["start"] = timezone.make_aware(dt.datetime.combine(date, t), timezone.utc)
        elif (date or t) and not start:
            self.add_error("start", "Укажите и дату, и время, или полностью поле «start».")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()
        return instance
