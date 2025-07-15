
from datetime import timedelta
from django.utils import timezone
from .models import KTPEntry, TemplateLesson, KTPTemplate, TemplateWeek

def get_template_schedule(template_week, subject, grade):
    return TemplateLesson.objects.filter(
        template_week=template_week,
        subject=subject,
        grade=grade
    ).order_by("day_of_week", "start_time")

def is_schedule_changed(old_week, new_week, subject, grade):
    old = get_template_schedule(old_week, subject, grade)
    new = get_template_schedule(new_week, subject, grade)

    old_set = set((l.day_of_week, l.start_time, l.teacher_id) for l in old)
    new_set = set((l.day_of_week, l.start_time, l.teacher_id) for l in new)

    return old_set != new_set

def get_next_week_start(date):
    return date - timedelta(days=date.weekday())

def generate_dates_from_template(ktp_template, start_date, template_week):
    entries = KTPEntry.objects.filter(section__ktp_template=ktp_template) \
        .select_related("section") \
        .order_by("section__order", "order")
    schedule = list(get_template_schedule(template_week, ktp_template.subject, ktp_template.grade))

    if not schedule:
        return 0

    week_start = get_next_week_start(start_date)
    entry_index = 0
    updated = 0

    while entry_index < len(entries):
        for lesson in schedule:
            if entry_index >= len(entries):
                break
            planned_date = week_start + timedelta(days=lesson.day_of_week)
            entry = entries[entry_index]
            entry.planned_date = planned_date
            entry.save(update_fields=["planned_date"])
            entry_index += 1
            updated += 1
        week_start += timedelta(weeks=1)

    # обновим ссылку на шаблон, который применяли
    ktp_template.last_template_week_used = template_week
    ktp_template.save(update_fields=["last_template_week_used"])
    return updated

def generate_dates_for_all_templates(start_date):
    new_template_week = TemplateWeek.objects.filter(is_active=True).last()
    updated_total = 0

    for ktp in KTPTemplate.objects.select_related("grade", "subject", "academic_year"):
        if not ktp.academic_year or not new_template_week:
            continue
        if ktp.last_template_week_used is None or is_schedule_changed(
            ktp.last_template_week_used, new_template_week, ktp.subject, ktp.grade
        ):
            updated_total += generate_dates_from_template(ktp, start_date, new_template_week)

    return updated_total
