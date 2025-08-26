import os
import sys
import django

# Добавить корень проекта в sys.path, если ты не в корне
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User
from schedule.core.models import (
    Grade, Subject, TeacherSubject, TeacherGrade, GradeSubject,
    TeacherAvailability, WeeklyNorm, LessonType, AcademicYear
)
from schedule.template.models import TemplateWeek, TemplateLesson, ActiveTemplateWeek
from datetime import time, timedelta, datetime

LESSON_DURATION = 45
LESSON_TYPE = LessonType.objects.get_or_create(key="lesson", defaults={"label": "Урок"})[0]
year = AcademicYear.objects.order_by("-id").first()
template_week, _ = TemplateWeek.objects.get_or_create(
    name="Шаблонная неделя №1", academic_year=year, is_active=True
)
ActiveTemplateWeek.objects.get_or_create(template=template_week)

grades = {
    "4А": Grade.objects.get(name="4А"),
    "5А": Grade.objects.get(name="5А"),
    "6А": Grade.objects.get(name="6А"),
}
subjects = {
    "История": Subject.objects.get(name="История"),
    "Русский язык": Subject.objects.get(name="Русский язык"),
    "Математика": Subject.objects.get(name="Математика"),
    "Информатика": Subject.objects.get(name="Информатика"),
}
teachers = {
    "Гуманитарий": User.objects.get(username="gumanitarij"),
    "Технарь": User.objects.get(username="tehnar"),
}
availability = {
    "Гуманитарий": dict((d, (time(8, 0), time(12, 0))) for d in range(5)),
    "Технарь": dict((d, (time(10, 0), time(13, 0))) for d in range(5)),
}
plan = [
    ("Гуманитарий", "4А", "История", 3),
    ("Гуманитарий", "4А", "Русский язык", 5),
    ("Гуманитарий", "5А", "История", 4),
    ("Гуманитарий", "5А", "Русский язык", 4),
    ("Технарь", "5А", "Математика", 5),
    ("Технарь", "5А", "Информатика", 3),
    ("Технарь", "6А", "Математика", 5),
    ("Технарь", "6А", "Информатика", 3),
]

def get_time_slots(start, end, count):
    slots = []
    dt = datetime.combine(datetime.today(), start)
    end_dt = datetime.combine(datetime.today(), end)
    while dt + timedelta(minutes=LESSON_DURATION) <= end_dt and len(slots) < count:
        slots.append(dt.time())
        dt += timedelta(minutes=LESSON_DURATION)
    return slots

day_offset = 0
for teacher_name, grade_name, subject_name, count in plan:
    grade = grades[grade_name]
    subject = subjects[subject_name]
    teacher = teachers[teacher_name]
    for n in range(count):
        day = (n + day_offset) % 5
        start, end = availability[teacher_name][day]
        busy_times = set(
            TemplateLesson.objects.filter(
                template_week=template_week,
                teacher=teacher,
                day_of_week=day
            ).values_list("start_time", flat=True)
        ) | set(
            TemplateLesson.objects.filter(
                template_week=template_week,
                grade=grade,
                day_of_week=day
            ).values_list("start_time", flat=True)
        )
        free_times = [t for t in get_time_slots(start, end, count) if t not in busy_times]
        if not free_times:
            print(f"❗ Не хватает слотов для {teacher} {grade} {subject} {day}")
            continue
        lesson_time = free_times[0]
        TemplateLesson.objects.create(
            template_week=template_week,
            grade=grade,
            subject=subject,
            teacher=teacher,
            day_of_week=day,
            start_time=lesson_time,
            duration_minutes=LESSON_DURATION,
            type=LESSON_TYPE
        )
    day_offset += 1

print("✅ Шаблонная неделя успешно заполнена уроками!")
