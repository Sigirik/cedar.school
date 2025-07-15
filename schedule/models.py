from django.db import models
from django.conf import settings
#from datetime import timedelta, datetime
from django.core.exceptions import ValidationError


# Дни недели: используется для выбора дня в расписании
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

# Учебный год (например: "2024–2025")
class AcademicYear(models.Model):
    name = models.CharField(max_length=20)  # Например: 2024-2025

    def __str__(self):
        return self.name

# Класс (группа учеников), например: "5А", "9Б"
class Grade(models.Model):
    name = models.CharField(max_length=100)  # Например: "5А", "9Б"

    def __str__(self):
        return self.name

# Учебный предмет, например: "Математика", "История"
class Subject(models.Model):
    name = models.CharField(max_length=100)  # Например: "Математика", "История"

    def __str__(self):
        return self.name

# Норма часов в неделю по предмету для каждого класса (по учебному плану)
class WeeklyNorm(models.Model):
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    hours_per_week = models.PositiveSmallIntegerField(help_text="Всего часов в неделю по предмету")
    lessons_per_week = models.PositiveSmallIntegerField(default=0, help_text="Уроков с учителем")
    courses_per_week = models.PositiveSmallIntegerField(default=0, help_text="Самостоятельных занятий (курсов)")

    class Meta:
        unique_together = ("grade", "subject")
        ordering = ["grade", "subject"]

    def __str__(self):
        return f"{self.grade} — {self.subject}: {self.hours_per_week} ч/нед"

# Доступность учителя по дням недели и времени — для составления расписания
class TeacherAvailability(models.Model):
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "TEACHER"}  # если понадобится
    )
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ("teacher", "day_of_week", "start_time", "end_time")
        ordering = ["teacher", "day_of_week", "start_time"]

    def __str__(self):
        return f"{self.teacher} — {WEEKDAYS[self.day_of_week]}: {self.start_time}–{self.end_time}"

# Шаблон недели (например, "Неделя №1") — основа для генерации расписания
class TemplateWeek(models.Model):
    name = models.CharField(max_length=100, help_text="Название шаблона (например: Неделя №1)")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Урок в шаблоне недели — используется для построения расписания
class TemplateLesson(models.Model):
    template_week = models.ForeignKey(TemplateWeek, on_delete=models.CASCADE)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "TEACHER"}
    )
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=45)

    class Meta:
        ordering = ["day_of_week", "start_time"]

    def __str__(self):
        return f"{self.template_week} | {self.grade} | {DAY_CHOICES[self.day_of_week][1]} {self.start_time} — {self.subject}"

    def clean(self):
        from users.models import UserSubject, UserGrade
        user = self.teacher
        is_superuser = getattr(user, "is_superuser", False)
        role = getattr(user, "role", None)

        # Проверка: входит ли день/время в доступное расписание
        available = TeacherAvailability.objects.filter(
            teacher=user,
            day_of_week=self.day_of_week,
            start_time__lte=self.start_time,
            end_time__gte=self.get_end_time()
        ).exists()

        if not available:
            if is_superuser or role in ["DIRECTOR", "HEAD_TEACHER"]:
                print(f"⚠️ Предупреждение: {user} вне времени занятости")
            else:
                raise ValidationError("Учитель недоступен в это время")

        # Проверка: преподаватель должен быть привязан к предмету
        if not UserSubject.objects.filter(teacher=self.teacher, subject=self.subject).exists():
            if is_superuser or role in ["DIRECTOR", "HEAD_TEACHER"]:
                print(f"⚠️ Предупреждение: {user} не привязан к предмету {self.subject}")
            else:
                raise ValidationError("Учитель не привязан к данному предмету")

        # Проверка: преподаватель должен быть привязан к классу
        if not UserGrade.objects.filter(teacher=self.teacher, grade=self.grade).exists():
            if is_superuser or role in ["DIRECTOR", "HEAD_TEACHER"]:
                print(f"⚠️ Предупреждение: {user} не привязан к классу {self.grade}")
            else:
                raise ValidationError("Учитель не привязан к данному классу")

    def get_end_time(self):
        from datetime import timedelta, datetime
        start = datetime.combine(datetime.today(), self.start_time)
        return (start + timedelta(minutes=self.duration_minutes)).time()

#Реальный урок в расписании
class RealLesson(models.Model):
    date = models.DateField()
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "TEACHER"}
    )
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)
    start_time = models.TimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=45)
    topic = models.CharField(max_length=255, blank=True)
    theme_from_ktp = models.CharField(max_length=255, blank=True)
    template_lesson = models.ForeignKey('TemplateLesson', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["date", "start_time"]

    def __str__(self):
        return f"{self.date} {self.grade} — {self.subject}"

    @property
    def end_time(self):
        from datetime import timedelta, datetime
        start = datetime.combine(self.date, self.start_time)
        return (start + timedelta(minutes=self.duration_minutes)).time()


# Шаблон КТП — объединяет тему, класс и учебный год.
# Пример: "КТП по математике 5А 2024–2025"
class KTPTemplate(models.Model):
    last_template_week_used = models.ForeignKey(
        'TemplateWeek', null=True, blank=True, on_delete=models.SET_NULL,
        help_text="Шаблон недели, по которому последний раз были распределены даты"
    )

    subject = models.ForeignKey('Subject', on_delete=models.CASCADE, related_name='ktp_templates')
    grade = models.ForeignKey('Grade', on_delete=models.CASCADE, related_name='ktp_templates')
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)  # Например: "КТП по математике 5А"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Раздел внутри шаблона КТП.
# Пример: "Тема 1: Натуральные числа", "Раздел 2: Геометрия"
class KTPSection(models.Model):
    ktp_template = models.ForeignKey(KTPTemplate, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField()
    hours = models.PositiveIntegerField(default=0)  # 🆕 Кол-во часов в разделе

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

# Конкретная запись КТП — одно занятие/урок.
# Пример: "Урок 1: Сложение натуральных чисел"
class KTPEntry(models.Model):
    LESSON_TYPE_CHOICES = [
        ('lesson', 'Урок'),
        ('course', 'Курс'),
    ]

    section = models.ForeignKey(KTPSection, on_delete=models.CASCADE, related_name='entries')
    lesson_number = models.PositiveIntegerField(default=1)  # 🆕 Номер урока в разделе
    type = models.CharField(max_length=10, choices=LESSON_TYPE_CHOICES, default='lesson')  # 🆕 Тип записи

    planned_date = models.DateField(blank=True, null=True)  # 🆕 Дата по плану
    actual_date = models.DateField(blank=True, null=True)  # 🆕 Дата по факту

    title = models.CharField(max_length=255)
    objectives = models.TextField(blank=True, null=True)
    tasks = models.TextField(blank=True, null=True)
    homework = models.TextField(blank=True, null=True)
    materials = models.TextField(blank=True, null=True)

    planned_outcomes = models.TextField(blank=True, null=True)  # 🆕 Планируемые результаты
    motivation = models.TextField(blank=True, null=True)        # 🆕 Мотивация

    order = models.PositiveIntegerField()

    template_lesson = models.ForeignKey(
        'TemplateLesson',  # строкой — если TemplateLesson ниже в файле
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

class TemplateWeekDraft(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    base_week = models.ForeignKey(TemplateWeek, on_delete=models.CASCADE)
    data = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Draft by {self.user} for {self.base_week.name}"
