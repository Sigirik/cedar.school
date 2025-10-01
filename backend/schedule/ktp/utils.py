"""
Модуль ktp/utils.py:
Вспомогательные функции для работы с датами уроков в КТП.
"""

from datetime import timedelta, date
from schedule.ktp.models import KTPEntry, KTPTemplate
from schedule.template.models import TemplateLesson

def get_template_schedule(template_week, subject, grade):
    """
    Возвращает уроки указанной шаблонной недели по предмету и классу.
    """
    return TemplateLesson.objects.filter(
        template_week=template_week,
        subject=subject,
        grade=grade
    ).order_by("day_of_week", "start_time")

def is_schedule_changed(old_template_week, new_template_week, subject, grade):
    """
    Проверяет, изменилось ли расписание между двумя шаблонными неделями.
    """
    old_lessons = get_template_schedule(old_template_week, subject, grade)
    new_lessons = get_template_schedule(new_template_week, subject, grade)

    old_set = set((lesson.day_of_week, lesson.start_time, lesson.teacher_id) for lesson in old_lessons)
    new_set = set((lesson.day_of_week, lesson.start_time, lesson.teacher_id) for lesson in new_lessons)

    return old_set != new_set

def get_next_monday(start_date=None):
    """
    Возвращает ближайший понедельник от указанной даты (или от текущей даты).
    """
    if not start_date:
        start_date = date.today()
    return start_date + timedelta(days=-start_date.weekday(), weeks=1)

def is_holiday_or_vacation(check_date):
    """
    Проверка на каникулы и праздники (заглушка).
    """
    # TODO: позже реализовать
    return False

def generate_ktp_dates_from_template(ktp_template, template_week, start_date=None):
    """
    Генерирует даты уроков КТП по указанной шаблонной неделе,
    начиная с указанной даты, учитывая каникулы и праздники.
    """
    if not start_date:
        start_date = get_next_monday()

    entries = KTPEntry.objects.filter(section__template=ktp_template)\
        .select_related("section")\
        .order_by("section__id", "lesson_number")

    schedule = list(get_template_schedule(template_week, ktp_template.subject, ktp_template.grade))

    if not schedule:
        return 0

    current_date = start_date
    updated_entries = 0
    entry_index = 0

    while entry_index < len(entries):
        weekday = current_date.weekday()

        if is_holiday_or_vacation(current_date):
            current_date += timedelta(days=1)
            continue

        daily_lessons = [lesson for lesson in schedule if lesson.day_of_week == weekday]

        for lesson in daily_lessons:
            if entry_index >= len(entries):
                break

            entry = entries[entry_index]
            entry.planned_date = current_date
            entry.save(update_fields=["planned_date"])
            entry_index += 1
            updated_entries += 1

        current_date += timedelta(days=1)

    ktp_template.last_template_week_used = template_week
    ktp_template.save(update_fields=["last_template_week_used"])

    return updated_entries
