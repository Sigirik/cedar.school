"""
Файл admin.py для приложения ktp:
Регистрирует модели календарно-тематических планов (КТП) в админке Django
и добавляет кастомные действия для управления датами уроков КТП.
"""

from django.contrib import admin, messages
from schedule.ktp.models import KTPEntry, KTPSection, KTPTemplate
from schedule.template.models import ActiveTemplateWeek
from schedule.ktp.utils import (
    generate_ktp_dates_from_template,
    get_next_monday,
    is_schedule_changed,
)

class KTPSectionInline(admin.TabularInline):
    model = KTPSection
    extra = 1

class KTPEntryInline(admin.TabularInline):
    model = KTPEntry
    extra = 0

@admin.register(KTPTemplate)
class KTPTemplateAdmin(admin.ModelAdmin):
    list_display = ["id", "subject", "grade", "academic_year", "name", "last_template_week_used"]
    list_filter = ["subject", "grade", "academic_year"]
    inlines = [KTPSectionInline]
    actions = ["generate_dates_for_selected_templates"]

    @admin.action(description="Генерировать даты уроков для выбранных КТП (активный шаблон недели)")
    def generate_dates_for_selected_templates(self, request, queryset):
        active_template_week = ActiveTemplateWeek.objects.select_related("template").last()
        if not active_template_week:
            self.message_user(request, "Нет активной шаблонной недели.", level=messages.ERROR)
            return

        template_week = active_template_week.template
        start_date = get_next_monday()
        total_updated = 0
        for ktp_template in queryset:
            if ktp_template.last_template_week_used is None or is_schedule_changed(
                ktp_template.last_template_week_used,
                template_week,
                ktp_template.subject,
                ktp_template.grade
            ):
                updated_entries = generate_ktp_dates_from_template(
                    ktp_template, template_week, start_date
                )
                total_updated += updated_entries

        self.message_user(request, f"Обновлено дат уроков: {total_updated}", level=messages.SUCCESS)


@admin.register(KTPSection)
class KTPSectionAdmin(admin.ModelAdmin):
    list_display = ["id", "ktp_template", "title", "description", "order"]
    list_filter = ["ktp_template"]
    search_fields = ["title", "ktp_template__subject__name", "ktp_template__grade__name"]
    inlines = [KTPEntryInline]

@admin.register(KTPEntry)
class KTPEntryAdmin(admin.ModelAdmin):
    list_display = [
        "id", "section", "lesson_number", "type", "planned_date", "actual_date", "title", "order", "template_lesson"
    ]
    list_filter = ["section__ktp_template__subject", "section__ktp_template__grade", "type"]
    search_fields = ["title", "section__title"]
