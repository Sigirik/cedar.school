from datetime import time
from collections import defaultdict

from schedule.models import (
    Subject, Grade, TeacherAvailability, TemplateWeek, TemplateLesson,
    AcademicYear, LessonType, WeeklyNorm
)
from users.models import User
def run():
    TemplateWeek.objects.filter(is_active=True).delete()

    year = AcademicYear.objects.first()
    if not year:
        year = AcademicYear.objects.create(name="2024–2025")

    subjects = {s.name: s for s in Subject.objects.all()}
    types = {t.key: t for t in LessonType.objects.all()}
    grades = list(Grade.objects.all())
    teachers = list(User.objects.filter(role="TEACHER"))

    availability_map = defaultdict(list)
    for a in TeacherAvailability.objects.all():
        availability_map[(a.teacher_id, a.day_of_week)].append((a.start_time, a.end_time))

    week = TemplateWeek.objects.create(name="Шаблон: тест без пересечений", academic_year=year, is_active=True)

    duration = 45
    days = [0, 1, 2, 3, 4]
    start_times = [time(9, 0), time(10, 0), time(11, 0), time(12, 0)]

    def find_teacher(subject_id, day, start, duration):
        for teacher in teachers:
            slots = availability_map.get((teacher.id, day), [])
            for slot_start, slot_end in slots:
                end_minutes = start.hour * 60 + start.minute + duration
                if slot_start <= start and end_minutes <= (slot_end.hour * 60 + slot_end.minute):
                    return teacher
        return None

    lessons = []
    for grade in grades:
        for day in days:
            time_index = 0
            for subject_name in ['Математика', 'Русский язык', 'История']:
                if time_index >= len(start_times): break
                start = start_times[time_index]
                time_index += 1
                subject = subjects[subject_name]
                teacher = find_teacher(subject.id, day, start, duration)
                if not teacher: continue
                lesson_type = types['course'] if day == 2 and subject_name == 'История' else types['lesson']
                lessons.append(TemplateLesson(
                    template_week=week,
                    subject=subject,
                    grade=grade,
                    teacher=teacher,
                    day_of_week=day,
                    start_time=start,
                    duration_minutes=duration,
                    type=lesson_type
                ))

    TemplateLesson.objects.bulk_create(lessons)
    print(f"✅ Создано {len(lessons)} уроков без пересечений.")
