from django.core.management.base import BaseCommand
from schedule.core.models import GradeSubject, AcademicYear
from schedule.ktp.models import KTPTemplate


class Command(BaseCommand):
    help = "Создаёт недостающие КТП-шаблоны для всех связок Класс + Предмет"

    def handle(self, *args, **kwargs):
        year = AcademicYear.objects.get(is_current=True)
        created = 0

        for gs in GradeSubject.objects.all():
            grade = gs.grade
            subject = gs.subject

            if not KTPTemplate.objects.filter(grade=grade, subject=subject, academic_year=year).exists():
                KTPTemplate.objects.create(
                    grade=grade,
                    subject=subject,
                    academic_year=year,
                    name=f"КТП по {subject.name} {grade.name}"
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Создано {created} новых КТП-шаблонов."))
