# schedule/real_schedule/forms.py
from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

from django import forms
from django.utils import timezone

from .models import RealLesson

UTC = ZoneInfo("UTC")


class RealLessonForm(forms.ModelForm):
    # Доп. удобство: раздельные вспомогательные поля (не из модели)
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        help_text="Дата начала (локальное время проекта)"
    )
    start_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
        help_text="Время начала (локальное время проекта)"
    )

    class Meta:
        model = RealLesson
        # Только реальные поля модели:
        fields = [
            "subject", "grade", "teacher",
            "start", "duration_minutes",
            "lesson_type", "topic_title", "ktp_entry",
            "source", "template_week_id", "template_lesson_id",
            "version", "conducted_at",
            "is_open",
        ]
        # ВАЖНО: НЕ задаём widget для "start" здесь — админ может подменить тип поля.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Заменяем admin-овский SplitDateTimeField на обычный DateTimeField
        # и даём несколько форматов ввода (RU и ISO).
        self.fields["start"] = forms.DateTimeField(
            required=False,
            widget=forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",  # чтобы <input type=datetime-local> работал корректно
                attrs={"type": "datetime-local"}
            ),
            input_formats=[
                "%Y-%m-%dT%H:%M",   # 2025-09-12T10:00 (браузер)
                "%Y-%m-%d %H:%M",   # 2025-09-12 10:00
                "%d.%m.%Y %H:%M",   # 12.09.2025 10:00 (RU)
            ],
            help_text="Либо заполните это поле, либо используйте пару «Дата» и «Время».",
        )

        # Инициализация вспомогательных полей из start (в локальной TZ проекта)
        if self.instance and self.instance.start:
            local = timezone.localtime(self.instance.start)
            self.fields["date"].initial = local.date()
            self.fields["start_time"].initial = local.time().replace(microsecond=0)

    def clean(self):
        cleaned = super().clean()
        d = cleaned.get("date")
        t = cleaned.get("start_time")
        start = cleaned.get("start")

        # Если указали раздельно дату/время — склеим в start
        if d and t:
            naive = dt.datetime.combine(d, t)  # локальное наивное
            aware_local = timezone.make_aware(naive, timezone.get_current_timezone())
            cleaned["start"] = aware_local.astimezone(UTC)
        elif (d or t) and not start:
            # если заполнили только одно из двух
            self.add_error("start", "Укажите и дату, и время, или полностью поле «start».")
        elif start:
            # если ввели единым полем — нормализуем в UTC (на всякий случай)
            if timezone.is_naive(start):
                start = timezone.make_aware(start, timezone.get_current_timezone())
            cleaned["start"] = start.astimezone(UTC)

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()
        return instance
