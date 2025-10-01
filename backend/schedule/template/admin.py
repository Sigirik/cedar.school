# schedule/template/admin.py
from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
from django import forms
from schedule.template.models import TemplateWeek, TemplateLesson
from schedule.ktp.utils import generate_ktp_dates_from_template
from .forms import TemplateLessonForm

@admin.register(TemplateLesson)
class TemplateLessonAdmin(admin.ModelAdmin):
    form = TemplateLessonForm
    list_display = ("template_week", "grade", "subject", "teacher", "day_of_week", "start_time", "duration_minutes")
    list_filter = ("template_week", "day_of_week", "teacher", "grade", "subject")
    search_fields = ("template_week__name", "grade__name", "teacher__username", "subject__name")

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)

class DateInputForm(forms.Form):
    start_date = forms.DateField(
        label="Дата начала применения шаблона",
        widget=forms.DateInput(attrs={'type': 'date'})
    )

@admin.register(TemplateWeek)
class TemplateWeekAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("recalculate/", self.admin_site.admin_view(self.recalculate_view), name="templateweek-recalculate"),
        ]
        return custom_urls + urls

    def recalculate_view(self, request):
        if request.method == "POST":
            form = DateInputForm(request.POST)
            if form.is_valid():
                start_date = form.cleaned_data["start_date"]
                updated = generate_ktp_dates_from_template(start_date)
                self.message_user(request, f"Обновлено {updated} записей КТП.", messages.SUCCESS)
                return redirect("..")
        else:
            form = DateInputForm()
        return render(request, "admin/recalculate_dates_form.html", {"form": form})
