from django.contrib import admin, messages
from .models import (
    AcademicYear,
    Grade,
    Subject,
    WeeklyNorm,
    TeacherAvailability,
    TemplateLesson,
    RealLesson,
    KTPTemplate,
    KTPSection,
    KTPEntry,
    TemplateWeekDraft,
)
from .forms import TemplateLessonForm
from .models import TemplateWeek
from django import forms
from django.shortcuts import render, redirect
from django.urls import path
from .ktp_utils import generate_dates_for_all_templates

@admin.register(TemplateLesson)
class TemplateLessonAdmin(admin.ModelAdmin):
    form = TemplateLessonForm
    list_display = ("template_week", "grade", "subject", "teacher", "day_of_week", "start_time", "duration_minutes")
    list_filter = ("template_week", "day_of_week", "teacher", "grade", "subject")
    search_fields = ("template_week__name", "grade__name", "teacher__username", "subject__name")

    def save_model(self, request, obj, form, change):
        # Валидируем данные перед сохранением
        obj.full_clean()
        super().save_model(request, obj, form, change)

admin.site.register(AcademicYear)
admin.site.register(Grade)
admin.site.register(Subject)
admin.site.register(WeeklyNorm)
admin.site.register(TeacherAvailability)
admin.site.register(RealLesson)
admin.site.register(TemplateWeekDraft)

class KTPEntryInline(admin.TabularInline):
    model = KTPEntry
    extra = 1

class KTPSectionInline(admin.TabularInline):
    model = KTPSection
    extra = 1

@admin.register(KTPTemplate)
class KTPTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'grade', 'academic_year')
    inlines = [KTPSectionInline]

@admin.register(KTPSection)
class KTPSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'ktp_template', 'order')
    inlines = [KTPEntryInline]

@admin.register(KTPEntry)
class KTPEntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'planned_date', 'actual_date', 'order', 'lesson_number', 'template_lesson')

class DateInputForm(forms.Form):
    start_date = forms.DateField(
        label="Дата начала применения шаблона",
        widget=forms.DateInput(attrs={'type': 'date'})
    )

@admin.register(TemplateWeek)
class TemplateWeekAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    #change_list_template = "admin/templateweek_changelist.html"

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
                updated = generate_dates_for_all_templates(start_date)
                self.message_user(request, f"Обновлено {updated} записей КТП.", messages.SUCCESS)
                return redirect("..")
        else:
            form = DateInputForm()
        return render(request, "admin/recalculate_dates_form.html", {"form": form})
