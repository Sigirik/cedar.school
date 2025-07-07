from datetime import date, timedelta
from schedule.models import TemplateLesson, RealLesson, TemplateWeek
from django.utils.timezone import make_aware
from django.db import transaction

# Начальная дата (например, понедельник 1 сентября 2025)
START_DATE = date(2025, 9, 1)

# Кол-во недель, на которые создаётся расписание
NUM_WEEKS = 2

# Название шаблона, по которому создаём
TEMPLATE_NAME = "Шаблонная неделя"

try:
    template_week = TemplateWeek.objects.get(name=TEMPLATE_NAME)
except TemplateWeek.DoesNotExist:
    print(f"❌ Шаблон недели '{TEMPLATE_NAME}' не найден.")
    exit()

lessons = TemplateLesson.objects.filter(template_week=template_week)

if not lessons.exists():
    print("❌ В шаблоне нет ни одного урока.")
    exit()

print(f"✅ Генерация расписания по шаблону: {TEMPLATE_NAME}")
created = 0

with transaction.atomic():
    for week in range(NUM_WEEKS):
        for lesson in lessons:
            # Расчёт даты на основе дня недели и недели вперёд
            weekday_offset = lesson.day_of_week
            lesson_date = START_DATE + timedelta(days=7 * week + weekday_offset)

            # Создание урока
            RealLesson.objects.create(
                date=lesson_date,
                day_of_week=lesson.day_of_week,
                subject=lesson.subject,
                teacher=lesson.teacher,
                grade=lesson.grade,
                start_time=lesson.start_time,
                duration_minutes=lesson.duration_minutes,
                template_lesson=lesson
            )
            created += 1

print(f"✅ Создано {created} уроков на {NUM_WEEKS} недели.")