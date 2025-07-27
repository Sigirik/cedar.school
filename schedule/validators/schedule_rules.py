#Проверки пересечений в расписании.
from datetime import datetime, timedelta
from schedule.core.models import TeacherSubject, TeacherGrade
from django.contrib.auth import get_user_model

User = get_user_model()

def get_lesson_end(lesson):
    start = datetime.strptime(lesson["start_time"], "%H:%M")
    end = start + timedelta(minutes=lesson["duration_minutes"])
    return start.time(), end.time()

def has_conflict(time_list):
    time_list.sort()
    for i in range(len(time_list) - 1):
        s1, e1 = time_list[i]
        s2, e2 = time_list[i + 1]
        if s2 < e1:
            return True
    return False

def validate_schedule(lessons: list[dict], weekly_norms: list[dict] = None, check_user_links: bool = False) -> tuple[list[str], list[str]]:
    """
    Проверяет список уроков и возвращает (ошибки, предупреждения)
    Ошибки блокируют сохранение, предупреждения — нет
    """
    errors = []
    warnings = []
    by_teacher = {}
    by_grade = {}
    by_subject_grade_type = {}

    teacher_cache = {}

    for lesson in lessons:
        teacher_id = lesson.get("teacher")
        grade_id = lesson.get("grade")
        subject_id = lesson.get("subject")
        lesson_type = lesson.get("type", "lesson")
        start_time_str = lesson.get("start_time")
        duration = lesson.get("duration_minutes")
        day = lesson.get("day_of_week")

        if not teacher_id or not subject_id:
            errors.append(f"🟥 Урок без предмета или учителя — день {day}, время {start_time_str}")
            continue

        try:
            start_time, end_time = get_lesson_end(lesson)
        except Exception:
            errors.append(f"⛔ Невалидное время у урока — день {day}, строка '{start_time_str}'")
            continue

        by_teacher.setdefault((teacher_id, day), []).append((start_time, end_time))
        by_grade.setdefault((grade_id, day), []).append((start_time, end_time))
        by_subject_grade_type[(grade_id, subject_id, lesson_type)] = by_subject_grade_type.get((grade_id, subject_id, lesson_type), 0) + 1

        # 🔍 Проверка связей учителя
        if check_user_links:
            teacher = teacher_cache.get(teacher_id)
            if not teacher:
                try:
                    teacher = User.objects.get(id=teacher_id)
                    teacher_cache[teacher_id] = teacher
                except User.DoesNotExist:
                    errors.append(f"⛔ Учитель ID={teacher_id} не найден в системе")
                    continue

            role = getattr(teacher, "role", None)
            is_superuser = getattr(teacher, "is_superuser", False)

            # Проверка предмета
            if not TeacherSubject.objects.filter(teacher=teacher, subject_id=subject_id).exists():
                if is_superuser or role in ["DIRECTOR", "HEAD_TEACHER"]:
                    warnings.append(f"⚠️ {teacher} не привязан к предмету ID={subject_id}")
                else:
                    errors.append(f"⛔ {teacher} не привязан к предмету ID={subject_id}")

            # Проверка класса
            if not TeacherGrade.objects.filter(teacher=teacher, grade_id=grade_id).exists():
                if is_superuser or role in ["DIRECTOR", "HEAD_TEACHER"]:
                    warnings.append(f"⚠️ {teacher} не привязан к классу ID={grade_id}")
                else:
                    errors.append(f"⛔ {teacher} не привязан к классу ID={grade_id}")

    for (teacher, day), times in by_teacher.items():
        if has_conflict(times):
            errors.append(f"⛔ Пересечение у учителя {teacher} в день {day}")

    for (grade, day), times in by_grade.items():
        if has_conflict(times):
            errors.append(f"⛔ Пересечение у класса {grade} в день {day}")

    # Проверка норм по (grade, subject, type)
    if weekly_norms:
        norm_map = {
            (n["grade"], n["subject"]): {
                "lesson": n.get("lessons_per_week", 0),
                "course": n.get("courses_per_week", 0)
            }
            for n in weekly_norms
        }
        for (grade, subject, lesson_type), count in by_subject_grade_type.items():
            expected = norm_map.get((grade, subject), {}).get(lesson_type, 0)
            if expected and count != expected:
                warnings.append(
                    f"⚠️ {grade} — {subject} ({'уроки' if lesson_type == 'lesson' else 'курсы'}): {count} из {expected}"
                )

    return errors, warnings