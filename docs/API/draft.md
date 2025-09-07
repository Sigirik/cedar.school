# Cedar.school API — Draft (TemplateWeekDraft)

Справочник по эндпоинтам модуля **draft**. Все запросы требуют авторизации (Bearer {{access_token}}).  
Переменная `access_token` берётся из логина (см. Core collection).

---

## 📚 Draft — TemplateWeekDraft

### 1. GET /api/draft/template-drafts/
Вернёт (или создаст, если нет) черновик текущего пользователя.  
**Ответ:** объект TemplateWeekDraft `{ id, user, base_week, data, change_history, ... }`.  
**Роли:** любой аутентифицированный пользователь【67†source】【68†source】.

---

### 2. POST /api/draft/template-drafts/create-from/
Создаёт черновик на основе шаблонной недели. Если `template_id` не указан — используется активная неделя.  
При этом предыдущий черновик пользователя удаляется.  
**Body (JSON):**
```json
{ "template_id": 123 }  // опционально
```  
**Роли:** любой аутентифицированный пользователь【67†source】【68†source】.

---

### 3. POST /api/draft/template-drafts/create-empty/
Создаёт пустой черновик (`data.lessons = []`). Удаляет предыдущий.  
**Роли:** аутентифицированные пользователи【67†source】【68†source】.

---

### 4. PATCH /api/draft/template-drafts/update/
Сохраняет новое содержимое черновика. Тело должно содержать ключ `data` с `{ "lessons": [...] }`.  
Перед сохранением текущее значение сохраняется в `change_history`.  
**Пример Body:**
```json
{
  "data": {
    "lessons": [
      {
        "subject": 10,
        "grade": 5,
        "teacher": 42,
        "day_of_week": 0,
        "start_time": "09:00",
        "duration_minutes": 45,
        "type": { "key": "lesson", "label": "Урок" }
      }
    ]
  }
}
```  
**Роли:** аутентифицированные пользователи【67†source】【68†source】.

---

### 5. POST /api/draft/template-drafts/<draft_id>/commit/
Публикация черновика как новой активной недели.  
- Текущая активная снимается с `is_active`.  
- Создаётся новая TemplateWeek и TemplateLesson из `data.lessons`.  
- Черновик очищается (`data.lessons = []`, `change_history = []`).  
**Роли:**  
- Владелец — может коммитить свой черновик.  
- Чужой черновик — только роли `ADMIN`, `DIRECTOR`, `HEAD_TEACHER`, `AUDITOR`【68†source】.

**Ответ:** `{ "detail": "Черновик опубликован", "week_id": <id> }`

---

### 6. GET /api/draft/template-drafts/exists/
Проверяет наличие черновика.  
**Ответ:** `{ "exists": true|false }`  
**Роли:** аутентифицированные пользователи【67†source】【68†source】.

---

### 7. POST /api/draft/template-drafts/validate/
Валидирует текущий черновик: проверка на коллизии (пересечения по времени/ресурсам).  
**Ответ:** `{ "lessons": [...], "collisions": [...] }`  
**Роли:** аутентифицированные пользователи【67†source】【68†source】.

---

## ⚙️ Использование в Postman
1. Выполните логин в Core → получите `access_token`.  
2. Выберите Environment с этой переменной.  
3. Все запросы Draft используют `Authorization: Bearer {{access_token}}`.  
4. Для Update/Commit используйте реальные id предметов, классов, учителей, а также корректные LessonType.
