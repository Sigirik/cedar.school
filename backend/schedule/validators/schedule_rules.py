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


from collections import defaultdict

def _collect_overlap_ids(items):
    # items: list[(start_time, end_time, lesson_id)]
    items = sorted(items, key=lambda x: (x[0], x[1]))
    n = len(items)
    pairs = set()
    for i in range(n):
        s1, e1, id1 = items[i]
        # сравниваем со всеми, начинающимися до конца i-го
        for j in range(i + 1, n):
            s2, e2, id2 = items[j]
            if s2 >= e1:
                break  # дальше все ещё позже
            pairs.add(tuple(sorted((id1, id2))))
    # объединяем пары в компоненты
    g = defaultdict(set)
    for a, b in pairs:
        g[a].add(b); g[b].add(a)
    visited, clusters = set(), []
    for node in {x for ab in pairs for x in ab}:
        if node in visited: continue
        stack, comp = [node], []
        while stack:
            v = stack.pop()
            if v in visited: continue
            visited.add(v); comp.append(v)
            stack.extend(g[v] - visited)
        clusters.append(sorted(comp))
    return clusters

def check_collisions(lessons: list[dict], include_warnings: bool = True) -> list[dict]:
    problems: list[dict] = []
    by_teacher = defaultdict(list)  # (teacher, day) -> [(s,e,id), ...]
    by_grade = defaultdict(list)

    for l in lessons:
        lid = l.get("id")
        teacher = l.get("teacher")
        grade = l.get("grade")
        day = l.get("day_of_week")
        try:
            s, e = get_lesson_end(l)
        except Exception:
            problems.append({
                "type": "invalid_time",
                "lesson_ids": [lid] if lid else [],
                "severity": "error",
                "message": f"Невалидное время — день {day}, строка '{l.get('start_time')}'"
            })
            continue

        if teacher: by_teacher[(teacher, day)].append((s, e, lid))
        if grade:   by_grade[(grade, day)].append((s, e, lid))

        if include_warnings:
            missing = [f for f in ("teacher","grade","subject") if not l.get(f)]
            if missing:
                problems.append({
                    "type": "missing_fields",
                    "lesson_ids": [lid] if lid else [],
                    "severity": "warning",
                    "message": "Не заполнены поля: " + ", ".join(missing)
                })

    for (tid, day), items in by_teacher.items():
        for cluster in _collect_overlap_ids(items):
            problems.append({
                "type": "teacher",
                "resource_id": tid,
                "weekday": day,
                "lesson_ids": cluster,
                "severity": "error",
                "message": f"Пересечение по teacher (id={tid}) в день {day}"
            })

    for (gid, day), items in by_grade.items():
        for cluster in _collect_overlap_ids(items):
            problems.append({
                "type": "grade",
                "resource_id": gid,
                "weekday": day,
                "lesson_ids": cluster,
                "severity": "error",
                "message": f"Пересечение по grade (id={gid}) в день {day}"
            })

    return problems