from django.db import models
from django.conf import settings

DAY_CHOICES = (
    (0, "Понедельник"),
    (1, "Вторник"),
    (2, "Среда"),
    (3, "Четверг"),
    (4, "Пятница"),
    (5, "Суббота"),
    (6, "Воскресенье"),
)

WEEKDAYS = dict(DAY_CHOICES)

class Grade(models.Model):
    name = models.CharField(max_length=20, unique=True)

    class Meta:
        verbose_name = "Grade"
        verbose_name_plural = "Классы"

    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Предметы"

    def __str__(self):
        return self.name

class TeacherAvailability(models.Model):
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='availabilities',
        limit_choices_to={"role": "TEACHER"}
    )
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ("teacher", "day_of_week", "start_time", "end_time")
        ordering = ["teacher", "day_of_week", "start_time"]
        verbose_name = "Доступность учителя"
        verbose_name_plural = "Доступность учителей"

    def __str__(self):
        return f"{self.teacher} — {WEEKDAYS[self.day_of_week]}: {self.start_time}–{self.end_time}"

class WeeklyNorm(models.Model):
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    lessons_per_week = models.PositiveSmallIntegerField(default=0, help_text="Уроков с учителем")
    courses_per_week = models.PositiveSmallIntegerField(default=0, help_text="Самостоятельных занятий (курсов)")

    class Meta:
        unique_together = ("grade", "subject")
        ordering = ["grade", "subject"]
        verbose_name = "WeeklyNorm"
        verbose_name_plural = "Недельные нормы"


    @property
    def hours_per_week(self):
        return self.lessons_per_week + self.courses_per_week

    def __str__(self):
        return f"{self.grade} — {self.subject}: {self.hours_per_week} ч/нед"

class LessonType(models.Model):
    key = models.CharField(max_length=32, unique=True)
    label = models.CharField(max_length=64)
    counts_towards_norm = models.BooleanField(default=True)

    class Meta:
        verbose_name = "LessonType"
        verbose_name_plural = "Типы уроков"

    def __str__(self):
        return self.label

class AcademicYear(models.Model):
    name = models.CharField(max_length=20)
    is_current = models.BooleanField(default=False)

    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        verbose_name = "AcademicYear"
        verbose_name_plural = "Учебные годы"

    def __str__(self):
        return self.name

class Quarter(models.Model):
    year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    name = models.CharField(max_length=10)  # I, II, III, IV
    start_date = models.DateField()
    end_date = models.DateField()

class Vacation(models.Model):
    year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    name = models.CharField()  # Осенние, Зимние...
    start_date = models.DateField()
    end_date = models.DateField()

class Holiday(models.Model):
    date = models.DateField(unique=True)
    name = models.CharField()
    type = models.CharField(
        max_length=20,
        choices=[
            ("official", "Официальный выходной"),
            ("custom", "Особый день"),
        ],
        default="official"
    )

# --- КТО с ЧЕМ связан: все связи расписания ---

class TeacherSubject(models.Model):
    """
    Какие предметы ведёт учитель (ранее UserSubject)
    """
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'TEACHER'},
        related_name="teaching_subjects"
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("teacher", "subject")
        verbose_name = "TeacherSubject"
        verbose_name_plural = "Учитель–предмет"

    def __str__(self):
        return f"{self.teacher} — {self.subject}"

class TeacherGrade(models.Model):
    """
    За какими классами закреплён учитель (ранее UserGrade)
    """
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'TEACHER'},
        related_name="teaching_grades"
    )
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("teacher", "grade")
        verbose_name = "TeacherGrade"
        verbose_name_plural = "Учитель–класс"

    def __str__(self):
        return f"{self.teacher} — {self.grade}"

class GradeSubject(models.Model):
    """
    Какие предметы есть у класса (учебный план для класса)
    """
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name="subjects")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("grade", "subject")
        verbose_name = "GradeSubject"
        verbose_name_plural = "Класс–предмет"

    def __str__(self):
        return f"{self.grade} — {self.subject}"

class StudentSubject(models.Model):
    """
    Индивидуальные предметы ученика (индивидуальные траектории)
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'STUDENT'},
        related_name="individual_subjects"
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)  # для быстрого поиска, необязательно

    class Meta:
        unique_together = ("student", "subject", "grade")
        verbose_name = "StudentSubject"
        verbose_name_plural = "Ученик–предмет"

    def __str__(self):
        return f"{self.student} — {self.subject} ({self.grade})"
