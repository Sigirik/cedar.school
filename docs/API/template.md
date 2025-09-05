# Cedar.school API — Template (Active Week & Lessons)

Эндпоинты для работы с шаблонными неделями и уроками.

---

## 📅 Active Week

### GET /api/template/active-week/
Возвращает текущую активную шаблонную неделю (последнюю по created_at).  
**Ответ:** объект TemplateWeek или 404, если активной недели нет【77†source】【78†source】.  
**Роли:** аутентифицированные пользователи.

---

## 🗓 Weeks

### GET /api/template/weeks/
Список всех шаблонных недель【77†source】【78†source】.

### GET /api/template/weeks/:id/
Получение конкретной недели по id【77†source】【78†source】.

---

## 📘 Lessons (TemplateLesson)

### GET /api/template/templatelesson/
Список всех уроков шаблонов【77†source】.

### GET /api/template/templatelesson/:id/
Получить урок по id.

### POST /api/template/templatelesson/
Создать новый урок.  
**Body пример:**
```json
{
  "week": 1,
  "grade": 5,
  "subject": 10,
  "teacher": 42,
  "day_of_week": 0,
  "start_time": "09:00",
  "duration_minutes": 45,
  "type": 1
}
```
### PATCH /api/template/templatelesson/:id/
Частично обновить урок.  
**Body пример:**
```json
{ "duration_minutes": 50 }
```

### DELETE /api/template/templatelesson/:id/
Удалить урок по id.

**Роли:** CRUD уроков доступен администраторам/руководителям (уточняется в permissions, по умолчанию ModelViewSet = аутентифицированные).

---

## ⚙️ Использование
- Все запросы требуют заголовок `Authorization: Bearer {{access_token}}`.  
- Для создания/обновления указывайте корректные id связных моделей (week, grade, subject, teacher, type).

