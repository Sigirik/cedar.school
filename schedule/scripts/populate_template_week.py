from schedule.models import TemplateWeek, TemplateLesson, Grade, Subject, TeacherAvailability
from users.models import UserGrade, UserSubject
from django.utils.timezone import now
from datetime import time

# Создаём шаблонную неделю
template_week, created = TemplateWeek.objects.get_or_create(name="Шаблонная неделя")

if not created:
    print("⚠️ Шаблонная неделя уже существует. Уроки будут добавлены, если их ещё нет.")

# Время начала уроков (две пары)
START_TIMES = [time(9, 0), time(10, 0)]

# Длительность уроков
DURATION = 45

# Дни недели (0 — понедельник, 4 — пятница)
DAYS = [0, 1, 2, 3, 4]

# Получаем существующих учителей, классы, предметы
grade_map = {}  # grade -> [subjects]
teacher_subjects = {}  # teacher -> [subjects]
teacher_grades = {}  # teacher -> [grades]

# Привязки учителей к классам и предметам
for user_grade in UserGrade.objects.select_related("teacher", "grade"):
    teacher_grades.setdefault(user_grade.teacher, []).append(user_grade.grade)

for user_subject in UserSubject.objects.select_related("teacher", "subject"):
    teacher_subjects.setdefault(user_subject.teacher, []).append(user_subject.subject)

# Расстановка уроков
count = 0

for teacher, subjects in teacher_subjects.items():
    grades = teacher_grades.get(teacher, [])
    for grade in grades:
        for day in DAYS:
            for i, start_time in enumerate(START_TIMES):
                if i >= len(subjects):
                    break
                subject = subjects[i]

                # Проверка дубликатов
                exists = TemplateLesson.objects.filter(
                    template_week=template_week,
                    grade=grade,
                    subject=subject,
                    teacher=teacher,
                    day_of_week=day,
                    start_time=start_time
                ).exists()

                if not exists:
                    TemplateLesson.objects.create(
                        template_week=template_week,
                        grade=grade,
                        subject=subject,
                        teacher=teacher,
                        day_of_week=day,
                        start_time=start_time,
                        duration_minutes=DURATION
                    )
                    count += 1

print(f"✅ Добавлено {count} уроков в шаблонную неделю.")