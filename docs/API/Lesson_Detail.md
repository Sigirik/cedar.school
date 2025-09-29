# 📄 Lesson Detail API

## GET `/api/real_schedule/lessons/{id}/`

Возвращает детальную карточку реального урока.

### Права доступа
- `ADMIN`, `HEAD_TEACHER`, `DIRECTOR` — доступ всегда (видят всех учеников).
- `TEACHER` — если назначен на урок (или в `co_teachers`, если поле используется).
- `STUDENT` — если подписан на предмет этого урока (`StudentSubject` по паре *(grade, subject)*) или добавлен индивидуально (через `LessonStudent`/M2M).
- `PARENT` — если связан с ребёнком (`ParentChild`) и у ребёнка есть подписка на предмет *(grade, subject)* или индивидуальное добавление в урок.

### Видимость списка учеников
- `ADMIN/HEAD_TEACHER/DIRECTOR/TEACHER` — **все** ученики.
- `PARENT` — **только свои дети**.
- `STUDENT` — **только себя**.

---

### Пример ответа 200 (MVP)

```json
{
  "id": 437,
  "subject": 5,
  "grade": 17,
  "teacher": 3,
  "date": "2025-09-02",
  "start_time": "09:00:00",
  "duration_minutes": 45,
  "room_name": null,
  "webinar_url": null,
  "topic": "Тема будет объявлена учителем в начале урока.",
  "materials": [],
  "participants": {
    "teachers": [3],
    "students_count": 28
  },
  "homework_summary": "",
  "students": [
    {
      "id": 101,
      "first_name": "Иван",
      "last_name": "Петров",
      "fio": "Петров Иван",
      "attendance": {
        "status": "late",
        "late_minutes": 7,
        "display": "опоздание 7 мин"
      },
      "mark": 4.0
    }
  ]
}
```

#### Поля ответа

| Поле | Тип | Описание |
|---|---|---|
| `id` | number | ID урока |
| `subject` | number | ID предмета |
| `grade` | number | ID класса/группы |
| `teacher` | number | ID основного учителя |
| `date` | string (YYYY-MM-DD) | Локальная дата начала урока |
| `start_time` | string (HH:MM:SS) | Локальное время начала |
| `duration_minutes` | number | Длительность урока в минутах |
| `room_name` | string \| null | Зарезервировано под офлайн-аудитории (на MVP `null`) |
| `webinar_url` | string \| null | Ссылка на онлайн-комнату (если есть `Room`) |
| `topic` | string | Тема урока (см. правила ниже) |
| `materials` | array | Заглушка под материалы (на MVP пустой массив) |
| `participants.teachers` | number[] | Все учителя урока (основной + `co_teachers`, если есть) |
| `participants.students_count` | number | Количество учеников по подписке на предмет *(grade, subject)* |
| `homework_summary` | string | Заглушка (на MVP пустая строка) |
| `students` | array | Список учеников в соответствии с правами просмотра (см. выше) |
| `students[].attendance.status` | "+" \| "-" \| "late" \| null | Статус посещаемости |
| `students[].attendance.late_minutes` | number \| null | Минуты опоздания (только при `late`) |
| `students[].attendance.display` | string \| null | Готовая строка для UI: "+", "-", "опоздание N мин" |
| `students[].mark` | number \| null | Оценка (если ведётся учётом `LessonStudent`) |

---

### Правила формирования ключевых полей

- **`topic`**:
  - если в `RealLesson.topic_title` есть значение — отдать его;
  - иначе для `STUDENT` и `PARENT` — дружелюбный фолбэк: **«Тема будет объявлена учителем в начале урока.»**;
  - для педсостава/админов — пустая строка `""`.

- **`participants.students_count`** — это `COUNT(StudentSubject)` для пары *(grade, subject)*.

- **`students[*].attendance` и `students[*].mark`** — берутся из `LessonStudent` (если модели нет — будут `null`).

- **`date` / `start_time`** — вычисляются из `start` с учётом настроек часового пояса проекта (`timezone.localtime`).

---

### Ошибки

- `401 Unauthorized` — без токена.
- `403 Forbidden` — нет прав согласно правилам выше.
- `404 Not Found` — урок не найден.

---

### Примеры запросов (cURL)

**Учитель своего урока** (видит всех):
```bash
curl -H "Authorization: Bearer $TEACHER_TOKEN"   http://localhost:8000/api/real_schedule/lessons/437/
```

**Ученик** (видит только себя; если тема не задана — фолбэк-текст):
```bash
curl -H "Authorization: Bearer $STUDENT_TOKEN"   http://localhost:8000/api/real_schedule/lessons/437/
```

**Родитель** (видит только своих детей):
```bash
curl -H "Authorization: Bearer $PARENT_TOKEN"   http://localhost:8000/api/real_schedule/lessons/437/
```

---

### Заметки

- Имя Django-роута: `lesson-detail`  
  (URL можно получать через `reverse("lesson-detail", kwargs={"id": <id>})`).
- Поле `co_teachers` опционально: если есть — учителя попадут в `participants.teachers`; если нет — игнорируется.
- Поле `room_name` зарезервировано под офлайн-аудитории; сейчас возвращается `null`.
- На фронтенде список учеников используется для показа ФИО и статусов; изменение статусов/оценок предполагается отдельными POST-эндпоинтами (вне данного метода).
