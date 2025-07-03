from users.models import User
from schedule.models import AcademicYear, Grade, Subject
from django.contrib.auth.hashers import make_password

# Учебный год
year, _ = AcademicYear.objects.get_or_create(name="2025-2026")

# Классы
grades = ["4А", "5А", "6А"]
for name in grades:
    Grade.objects.get_or_create(name=name)

# Предметы
subjects = ["Математика", "Русский язык", "Английский язык", "История"]
for name in subjects:
    Subject.objects.get_or_create(name=name)

# Учителя
teachers = [
    {"username": "gumanitarii", "first_name": "Гуманитарий"},
    {"username": "technar", "first_name": "Технарь"},
]

for t in teachers:
    User.objects.get_or_create(
        username=t["username"],
        defaults={
            "first_name": t["first_name"],
            "password": make_password("test1234"),
            "role": User.Role.TEACHER,
        },
    )

print("✅ Данные добавлены.")