# backend/scripts/seed_school_basics.py
import os
import sys
from datetime import date
from pathlib import Path

# --- Django bootstrap (поправь DJANGO_SETTINGS_MODULE под свой проект!)
BASE_DIR = Path(__file__).resolve().parents[1]  # backend/
PROJECT_ROOT = BASE_DIR  # если settings.py лежит в backend/settings.py
sys.path.append(str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from django.db import transaction
from django.apps import apps

def find_model(model_name: str):
    for m in apps.get_models():
        if m.__name__ == model_name:
            return m
    raise LookupError(f"Model {model_name} not found in INSTALLED_APPS")

@transaction.atomic
def seed():
    GradeLevel   = find_model("GradeLevel")
    Parallel     = find_model("Parallel")
    Grade        = find_model("Grade")
    Subject      = find_model("Subject")
    GradeSubject = find_model("GradeSubject")
    WeeklyNorm   = find_model("WeeklyNorm")
    LessonType   = find_model("LessonType")
    AcademicYear = find_model("AcademicYear")

    # 1.1 Ступени 1..11
    for n in range(1, 12):
        GradeLevel.objects.get_or_create(number=n)
    print("GradeLevels 1..11 OK")

    # 1.2 Параллели А, Б
    pA, _ = Parallel.objects.get_or_create(code="А", defaults={"title": "Параллель А"})
    pB, _ = Parallel.objects.get_or_create(code="Б", defaults={"title": "Параллель Б"})
    print("Parallels A,B OK")

    # 1.3 Классы 1А..11Б
    levels = {gl.number: gl for gl in GradeLevel.objects.all()}
    grades = []
    for num in range(1, 12):
        for p in (pA, pB):
            name = f"{num}{p.code}"
            g, _ = Grade.objects.get_or_create(
                name=name,
                defaults={"level": levels[num], "parallel": p}
            )
            changed = False
            if g.level_id is None:
                g.level = levels[num]; changed = True
            if g.parallel_id is None:
                g.parallel = p; changed = True
            if changed:
                g.save()
            grades.append(g)
    print(f"Grades {len(grades)} OK")

    # 2. Предметы
    subject_names = ["Математика", "Русский язык", "Английский язык", "Чтение", "Окружающий мир"]
    subjects = {}
    for s in subject_names:
        subj, _ = Subject.objects.get_or_create(name=s)
        subjects[s] = subj
    print("Subjects OK")

    # 3. Grade–Subject через GradeSubject
    created_gs = 0
    for g in grades:
        level_num = g.level.number if g.level_id else int("".join(ch for ch in g.name if ch.isdigit()))
        to_assign = set()
        if 1 <= level_num <= 4:
            to_assign.update(subject_names)  # все 5
        if 5 <= level_num <= 6:
            to_assign.add("Математика")
        to_assign.update(["Русский язык", "Английский язык"])
        for sname in to_assign:
            subj = subjects.get(sname)
            if not subj:
                continue
            _, created = GradeSubject.objects.get_or_create(grade=g, subject=subj)
            if created:
                created_gs += 1
    print(f"GradeSubject created {created_gs}")

    # 4. Недельные нормы
    norm_map = {"Математика": 5, "Русский язык": 5, "Английский язык": 3}
    set_norms = 0
    for g in grades:
        for sname, value in norm_map.items():
            subj = subjects[sname]
            obj, created = WeeklyNorm.objects.get_or_create(
                grade=g, subject=subj,
                defaults={"lessons_per_week": value}
            )
            if not created and obj.lessons_per_week != value:
                obj.lessons_per_week = value
                obj.save(update_fields=["lessons_per_week"])
            set_norms += 1
    print(f"WeeklyNorm set/updated {set_norms}")

    # 5. Типы уроков
    types = [
        ("lesson",   "Обычный",     True),
        ("practice", "Практика",    True),
        ("test",     "Контрольная", True),
        ("exam",     "Экзамен",     False),
        ("meeting",  "Собрание",    False),
    ]
    for key, label, counts in types:
        obj, _ = LessonType.objects.get_or_create(
            key=key,
            defaults={"label": label, "counts_towards_norm": counts}
        )
        changed = False
        if obj.label != label:
            obj.label = label; changed = True
        if obj.counts_towards_norm != counts:
            obj.counts_towards_norm = counts; changed = True
        if changed:
            obj.save(update_fields=["label", "counts_towards_norm"])
    print("LessonTypes OK")

    # 6. Учебный год 2025–2026
    start, end = date(2025, 9, 1), date(2026, 6, 15)
    ay, created = AcademicYear.objects.get_or_create(
        name="2025–2026",
        defaults={"start_date": start, "end_date": end, "is_current": True}
    )
    changed = False
    if ay.start_date != start:
        ay.start_date = start; changed = True
    if ay.end_date != end:
        ay.end_date = end; changed = True
    if not ay.is_current:
        ay.is_current = True; changed = True
    if changed:
        ay.save(update_fields=["start_date", "end_date", "is_current"])
    # сбросим текущесть у остальных
    AcademicYear.objects.exclude(pk=ay.pk).filter(is_current=True).update(is_current=False)
    print("AcademicYear 2025–2026 OK (current)")

if __name__ == "__main__":
    seed()
    print("Seed finished.")
