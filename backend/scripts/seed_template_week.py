# backend/scripts/seed_template_week.py
import os, sys
from pathlib import Path
from datetime import time, datetime, timedelta
from collections import Counter

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from django.db import transaction
from django.apps import apps

def M(name):
    for m in apps.get_models():
        if m.__name__ == name:
            return m
    raise LookupError(f"Model {name} not found")

TemplateWeek    = M("TemplateWeek")
TemplateLesson  = M("TemplateLesson")
AcademicYear    = M("AcademicYear")
Subject         = M("Subject")
Grade           = M("Grade")
WeeklyNorm      = M("WeeklyNorm")
LessonType      = M("LessonType")
User            = M("User")
TeacherSubject  = M("TeacherSubject")
TeacherGrade    = M("TeacherGrade")
TeacherAvail    = M("TeacherAvailability")

# --- параметры ---
GRADES_LEVELS   = [5, 6, 7]
SUBJECT_NAMES   = ["Математика", "Русский язык", "История", "Информатика"]
DAYS            = [0,1,2,3,4]   # Пн–Пт
DURATION_MIN    = 45
BREAK_MIN       = 15
HOUR_SLOTS      = [8,9,10,11,12,13]  # старт ровно в :00

TECH_SUBJECTS   = {"Математика", "Информатика"}
HUM_SUBJECTS    = {"Русский язык", "История"}

def tadd(t: time, minutes: int) -> time:
    ref = datetime.combine(datetime.today(), t)
    return (ref + timedelta(minutes=minutes)).time()

def fits_window(start: time, dur: int, a_start: time, a_end: time) -> bool:
    end_m = start.hour*60 + start.minute + dur
    return a_start <= start and end_m <= (a_end.hour*60 + a_end.minute)

def build_availability_map():
    amap = {}
    for a in TeacherAvail.objects.all():
        dow = getattr(a, "day_of_week", getattr(a, "weekday", None))
        amap.setdefault((a.teacher_id, dow), []).append((a.start_time, a.end_time))
    return amap

def get_teacher_by_username(username: str):
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        return None

def ensure_subjects():
    existing = {s.name: s for s in Subject.objects.filter(name__in=SUBJECT_NAMES)}
    created = []
    for n in SUBJECT_NAMES:
        if n not in existing:
            existing[n] = Subject.objects.create(name=n)
            created.append(n)
    if created:
        print(f"[INFO] Созданы недостающие предметы: {', '.join(created)}")
    return existing

def get_norm(norm_map, grade_id, subj_id, fallback=1):
    v = norm_map.get((grade_id, subj_id))
    return v if v is not None else fallback

def compute_targets(norm_map, subjects_by_name, grade_id, total=10):
    # базовые от норм
    tgt = {
        "Математика":   get_norm(norm_map, grade_id, subjects_by_name["Математика"].id, fallback=4),
        "Русский язык": max(get_norm(norm_map, grade_id, subjects_by_name["Русский язык"].id, fallback=4) - 1, 0),
        "История":      get_norm(norm_map, grade_id, subjects_by_name["История"].id, fallback=1) + 1,
        "Информатика":  get_norm(norm_map, grade_id, subjects_by_name["Информатика"].id, fallback=1),
    }
    # минимум по 1
    for k in list(tgt.keys()):
        tgt[k] = max(tgt[k], 1)
    # нормируем до total
    s = sum(tgt.values())
    if s > total:
        order = ["Информатика", "История", "Русский язык", "Математика"]
        i = 0
        while s > total and i < len(order):
            k = order[i]
            if tgt[k] > 1:
                tgt[k] -= 1; s -= 1
            else:
                i += 1
    elif s < total:
        order = ["Математика", "Русский язык", "История", "Информатика"]
        i = 0
        while s < total:
            tgt[order[i % 4]] += 1; s += 1; i += 1
    return tgt

@transaction.atomic
def main():
    # 0) активная неделя начисто
    TemplateWeek.objects.filter(is_active=True).delete()
    year = AcademicYear.objects.order_by("-start_date").first() or AcademicYear.objects.create(name="2025–2026")

    # 1) справочники
    subjects = ensure_subjects()
    grades = list(Grade.objects.filter(level__number__in=GRADES_LEVELS).order_by("level__number","name"))
    if not grades:
        print("⛔ Нет классов 5/6/7 — прерываю."); return
    grades_by_id = {g.id: g for g in grades}

    # учителя **жёстко** по ролям:
    technar = get_teacher_by_username("Tehnar")
    guman   = get_teacher_by_username("Gumanitarii")
    if not technar or not guman:
        print("⛔ Не найдены пользователи 'Tehnar' и/или 'Gumanitarii' — прерываю."); return

    # карта доступностей
    A = build_availability_map()

    # норматива
    norm_map = {}
    for g in grades:
        for s in subjects.values():
            wn = WeeklyNorm.objects.filter(grade=g, subject=s).first()
            norm_map[(g.id, s.id)] = wn.lessons_per_week if wn else None

    lt_lesson = LessonType.objects.filter(key="lesson").first() or LessonType.objects.first()

    # 2) квоты (по 10 на класс)
    quotas = {g.id: compute_targets(norm_map, subjects, g.id, total=10) for g in grades}
    if sum(sum(c.values()) for c in quotas.values()) != 30:
        print("[WARN] Квоты не равны 30 — будет нормализация в процессе раскладки.")

    # 3) создаём неделю
    week = TemplateWeek.objects.create(
        name="Шаблон: 5–7 классы (30 уроков, без пересечений)",
        academic_year=year, is_active=True,
        description="2 урока/день на класс; Технарь=Матем/Информ, Гуман=Рус/Ист; История +1, Русский -1 от нормы."
    )

    lessons = []

    # удобные слоты для каждого учителя
    TECH_SLOTS = [time(8,0), time(9,0), time(10,0)]                 # из его доступности 08–11
    HUM_SLOTS  = [time(11,0), time(12,0), time(9,0), time(10,0), time(13,0)]  # 09–13, но стараемся позже, чтобы не пересекать класс

    # Проверка доступности слота у конкретного учителя в день
    def teacher_slot_ok(teacher, dow, start):
        for (a_start, a_end) in A.get((teacher.id, dow), []):
            if fits_window(start, DURATION_MIN, a_start, a_end):
                # нет ли уже урока у этого учителя в этот момент
                for l in lessons:
                    if l.teacher_id == teacher.id and l.day_of_week == dow:
                        l_end = tadd(l.start_time, l.duration_minutes)
                        s_end = tadd(start, DURATION_MIN)
                        if not (l_end <= start or s_end <= l.start_time):
                            return False
                return True
        return False

    # Проверка занятости класса
    def grade_slot_free(grade_id, dow, start):
        return not any(l.grade_id == grade_id and l.day_of_week == dow and l.start_time == start for l in lessons)

    # 4) раскладка: по дню каждому классу ставим 1 “тех”-предмет и 1 “гум”-предмет
    for dow in DAYS:
        # распределим тех-уроки по трём слотам 8/9/10 — каждому классу свой, чтобы Технарь не пересекался
        tech_slots_cycle = list(TECH_SLOTS)  # 3 штуки → по одной на класс
        hum_slots_cycle  = list(HUM_SLOTS)

        for g in grades:
            # --- 4.1 выбрать предметы на сегодня: один из TECH_SUBJECTS и один из HUM_SUBJECTS (по максимуму остатка)
            q = quotas[g.id]
            def best_from(names):
                remaining = [(name, q.get(name, 0)) for name in names]
                remaining.sort(key=lambda kv: kv[1], reverse=True)
                for n, c in remaining:
                    if c > 0:
                        return n
                return None

            tech_subj_name = best_from(TECH_SUBJECTS)
            hum_subj_name  = best_from(HUM_SUBJECTS)

            # --- 4.2 поставить тех-урок
            if tech_subj_name and tech_slots_cycle:
                start = None
                # найдём свободный слот из приоритета 8→9→10
                while tech_slots_cycle and start is None:
                    cand = tech_slots_cycle.pop(0)
                    if grade_slot_free(g.id, dow, cand) and teacher_slot_ok(technar, dow, cand):
                        start = cand
                if start:
                    lessons.append(TemplateLesson(
                        template_week=week, grade=g, subject=subjects[tech_subj_name],
                        teacher=technar, day_of_week=dow, start_time=start,
                        duration_minutes=DURATION_MIN, type=lt_lesson
                    ))
                    q[tech_subj_name] -= 1

            # --- 4.3 поставить гум-урок (стараемся в 11/12, чтобы не прилегал к тех-уроку у этого же класса)
            if hum_subj_name and hum_slots_cycle:
                start = None
                # выберем первый слот, где класс свободен и гуманитарий свободен
                # предпочтительно 11/12, затем 9/10/13
                for i, cand in enumerate(list(hum_slots_cycle)):
                    if grade_slot_free(g.id, dow, cand) and teacher_slot_ok(guman, dow, cand):
                        start = cand
                        hum_slots_cycle.pop(i)
                        break
                if start:
                    lessons.append(TemplateLesson(
                        template_week=week, grade=g, subject=subjects[hum_subj_name],
                        teacher=guman, day_of_week=dow, start_time=start,
                        duration_minutes=DURATION_MIN, type=lt_lesson
                    ))
                    q[hum_subj_name] -= 1

    # 5) добить “хвосты” (если по квотам ещё остались)
    for dow in DAYS:
        for g in grades:
            q = quotas[g.id]
            # пока нужно и есть свободные слоты — попробуем дозаложить, соблюдая закрепление преподавателей
            for subj_name, left in sorted(q.items(), key=lambda kv: kv[1], reverse=True):
                while left > 0:
                    teacher = technar if subj_name in TECH_SUBJECTS else guman
                    candidates = TECH_SLOTS if teacher == technar else HUM_SLOTS
                    placed = False
                    for cand in candidates:
                        if grade_slot_free(g.id, dow, cand) and teacher_slot_ok(teacher, dow, cand):
                            lessons.append(TemplateLesson(
                                template_week=week, grade=g, subject=subjects[subj_name],
                                teacher=teacher, day_of_week=dow, start_time=cand,
                                duration_minutes=DURATION_MIN, type=lt_lesson
                            ))
                            q[subj_name] -= 1
                            left -= 1
                            placed = True
                            break
                    if not placed:
                        break  # в этот день не удалось — попробуем в другом

    # 6) нормируем до ровно 30 уроков
    if len(lessons) > 30:
        lessons = lessons[:30]
    elif len(lessons) < 30:
        # добавим математику там, где возможно, соблюдая правила
        for dow in DAYS:
            for g in grades:
                if len(lessons) >= 30:
                    break
                for cand in TECH_SLOTS:
                    if grade_slot_free(g.id, dow, cand) and teacher_slot_ok(technar, dow, cand):
                        lessons.append(TemplateLesson(
                            template_week=week, grade=g, subject=subjects["Математика"],
                            teacher=technar, day_of_week=dow, start_time=cand,
                            duration_minutes=DURATION_MIN, type=lt_lesson
                        ))
                        break
            if len(lessons) >= 30:
                break

    TemplateLesson.objects.bulk_create(lessons)
    print(f"✅ Создано {len(lessons)} уроков в '{week.name}' (ожидалось 30)")

if __name__ == "__main__":
    main()
