# backend/scripts/seed_ktp_basic.py
import os
import sys
from pathlib import Path
from datetime import date

BASE_DIR = Path(__file__).resolve().parents[1]  # backend/
sys.path.append(str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from django.db import transaction
from django.apps import apps

def M(name: str):
    for m in apps.get_models():
        if m.__name__ == name:
            return m
    raise LookupError(f"Model {name} not found")

# === модели из проекта ===
# KTP
KTPTemplate  = M("KTPTemplate")
KTPSection   = M("KTPSection")
KTPEntry     = M("KTPEntry")
# ядро
Subject      = M("Subject")
Grade        = M("Grade")
AcademicYear = M("AcademicYear")
TemplateWeek = M("TemplateWeek")
# пользователи/связи
User            = M("User")
TeacherSubject  = M("TeacherSubject")
TeacherGrade    = M("TeacherGrade")

# параметры задачи
SUBJECTS = ["Математика", "Русский язык", "История", "Информатика"]
GRADE_LEVELS = [5, 6, 7]

# «жёсткая» привязка предметов к учителям по username
TEACHER_BY_SUBJECT = {
    "Математика":   "Tehnar",
    "Информатика":  "Tehnar",
    "Русский язык": "Gumanitarii",
    "История":      "Gumanitarii",
}

def get_academic_year():
    ay = AcademicYear.objects.filter(is_current=True).first()
    if not ay:
        # если нет — берём последний по дате или создаём 2025–2026
        ay = AcademicYear.objects.order_by("-start_date").first()
    if not ay:
        ay = AcademicYear.objects.create(
            name="2025–2026",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 6, 15),
            is_current=True
        )
    return ay

def get_teacher(username: str):
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        return None

def section_title(subject_name: str, idx: int) -> str:
    # Просто удобные заголовки
    base = {
        "Математика": "Раздел: Алгебра и начало анализа",
        "Русский язык": "Раздел: Развитие речи и грамматика",
        "История": "Раздел: История Отечества",
        "Информатика": "Раздел: Алгоритмы и данные",
    }.get(subject_name, "Раздел")
    return f"{base} #{idx}"

def topic_title(subject_name: str, section_idx: int, lesson_idx: int) -> str:
    return f"{subject_name}: Тема {section_idx}.{lesson_idx}"

@transaction.atomic
def main():
    ay = get_academic_year()

    # неделя-шаблон, к которой можно «привязать» КТП (опционально)
    last_week = TemplateWeek.objects.filter(academic_year=ay).order_by("-id").first()

    # подготовим справочники
    subj_by_name = {s.name: s for s in Subject.objects.filter(name__in=SUBJECTS)}
    missing = [n for n in SUBJECTS if n not in subj_by_name]
    if missing:
        print(f"[INFO] Эти предметы не найдены и будут пропущены: {', '.join(missing)}")

    # классы 5–7 (можно иметь несколько параллелей — заведём КТП для каждого класса уровня)
    grades = list(Grade.objects.filter(level__number__in=GRADE_LEVELS).order_by("level__number", "name"))
    if not grades:
        print("⛔ Не найдены классы 5–7. Останавливаюсь.")
        return

    created_ktp = 0
    created_sections = 0
    created_entries = 0
    skipped_pairs = []

    for g in grades:
        for subj_name, teacher_username in TEACHER_BY_SUBJECT.items():
            # пропустим предмет, если его нет в БД
            subj = subj_by_name.get(subj_name)
            if not subj:
                skipped_pairs.append((g.name, subj_name, "нет предмета в БД"))
                continue

            # найдём нужного учителя
            teacher = get_teacher(teacher_username)
            if not teacher:
                skipped_pairs.append((g.name, subj_name, f"учитель {teacher_username} не найден"))
                continue

            # проверим связи учителя: предмет и класс
            if not TeacherSubject.objects.filter(teacher=teacher, subject=subj).exists():
                skipped_pairs.append((g.name, subj_name, f"учитель {teacher_username} не привязан к предмету"))
                continue
            if not TeacherGrade.objects.filter(teacher=teacher, grade=g).exists():
                skipped_pairs.append((g.name, subj_name, f"учитель {teacher_username} не привязан к классу"))
                continue

            # Название КТП
            ktp_name = f"КТП по {subj_name.lower()} {g.name} {ay.name}"
            ktp, created = KTPTemplate.objects.get_or_create(
                subject=subj, grade=g, academic_year=ay,
                defaults={"name": ktp_name, "last_template_week_used": last_week},
            )
            if not created and (ktp.name != ktp_name or ktp.last_template_week_used_id != (last_week.id if last_week else None)):
                ktp.name = ktp_name
                ktp.last_template_week_used = last_week
                ktp.save(update_fields=["name", "last_template_week_used"])
            if created:
                created_ktp += 1

            # 2 раздела по 10 тем каждый (итого 20 записей на КТП)
            for s_idx in (1, 2):
                sec, s_created = KTPSection.objects.get_or_create(
                    ktp_template=ktp, order=s_idx,
                    defaults={
                        "title": section_title(subj_name, s_idx),
                        "description": "",
                        "hours": 10,  # условно ставим 10 часов на раздел
                    }
                )
                if s_created:
                    created_sections += 1
                else:
                    # убедимся, что заголовок/часы актуальны
                    changed = False
                    new_title = section_title(subj_name, s_idx)
                    if sec.title != new_title:
                        sec.title = new_title; changed = True
                    if sec.hours != 10:
                        sec.hours = 10; changed = True
                    if changed:
                        sec.save(update_fields=["title", "hours"])

                # Создаём 10 тем (уроков) в разделе
                # Нумерация lesson_number и order — 1..10 внутри раздела
                for i in range(1, 11):
                    entry, e_created = KTPEntry.objects.get_or_create(
                        section=sec, order=i,
                        defaults={
                            "lesson_number": i,
                            "type": "lesson",
                            "title": topic_title(subj_name, s_idx, i),
                            "objectives": "",
                            "tasks": "",
                            "homework": "",
                            "materials": "",
                            "planned_outcomes": "",
                            "motivation": "",
                            "planned_date": None,
                            "actual_date": None,
                            "template_lesson_id": None,
                        }
                    )
                    if e_created:
                        created_entries += 1
                    else:
                        # При повторном запуске — мягкое обновление только заголовка/номера,
                        # чтобы не затирать вручную заполненные поля.
                        need_title = topic_title(subj_name, s_idx, i)
                        changed = False
                        if entry.title != need_title:
                            entry.title = need_title; changed = True
                        if entry.lesson_number != i:
                            entry.lesson_number = i; changed = True
                        if changed:
                            entry.save(update_fields=["title", "lesson_number"])

    print(f"✅ KTP: создано {created_ktp}, разделов: {created_sections}, тем (записей): {created_entries}")
    if skipped_pairs:
        print("ℹ️ Пропущенные пары (класс, предмет, причина):")
        for gname, sname, reason in skipped_pairs:
            print(f" - {gname}: {sname} — {reason}")

if __name__ == "__main__":
    main()
