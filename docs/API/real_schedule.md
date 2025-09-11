# Cedar.school API — Real Schedule

Эндпоинты реального расписания: «моё расписание», общий листинг с фильтрами, просмотр «как видит пользователь», детальная карточка урока, генерация, проведение урока и комнаты видеозанятий, а также справочники (минимально — учителя).

---

## 🔐 Авторизация и форматы

- Каждый запрос требует заголовок:  
  `Authorization: Bearer <JWT>`
- Даты в query — **ISO `YYYY-MM-DD`**.
- Диапазон дат валидируется и **не может превышать 31 день**.
- Таймзона по умолчанию на выдаче — **Europe/Moscow (МСК)**. Для локализации времени клиент может передать заголовок `X-TZ: <IANA TZ>` (например, `Europe/Moscow`, `Asia/Almaty`). Если TZ пользователя = МСК±0 — пометку “(МСК ±N)” на фронте можно **не** отображать.
- Если `from`/`to` не указаны — используется **школьная неделя по умолчанию** (Mon–Sun) текущего учебного периода.

---

## 👤 My schedule

### `GET /api/real_schedule/my/?from=&to=&children=`

Выдаёт расписание **для текущего пользователя** за указанный период.

**Роли и видимость**
- `ADMIN`, `DIRECTOR`, `HEAD_TEACHER`, `METHODIST`, `AUDITOR` — видят все уроки.
- `TEACHER` — видит только свои уроки.
- `STUDENT` — видит свои уроки (по классу/индивидуальным предметам).
- `PARENT` — агрегировано по активным детям; можно сузить `children=1,2` (список id детей).

**Параметры (query)**
- `from`, `to` — `YYYY-MM-DD`. При отсутствии берётся неделя по умолчанию (Mon–Sun).
- `children` — строка вида "1,2,3" (только для роли `PARENT`).

**Ответ 200**
```json
{
  "from": "YYYY-MM-DD",
  "to": "YYYY-MM-DD",
  "count": 3,
  "results": [
    {
      "id": 101,
      "subject": 5,
      "grade": 12,
      "teacher": 77,
      "date": "2025-09-01",
      "start_time": "10:00:00",
      "duration_minutes": 45,
      "type": "lesson",
      "room": null
    }
  ]
}
```

**Ошибки**: `400 INVALID_RANGE / RANGE_TOO_WIDE`, `401`, `403`.

---

## 📋 Lessons — общий список с фильтрами (новое)

### `GET /api/real_schedule/lessons/`

**Доступ:** `ADMIN`, `DIRECTOR`, `HEAD_TEACHER`, `METHODIST`, `AUDITOR` (read-only).

**Параметры (query)**
- `from`, `to` — `YYYY-MM-DD`. Если не заданы — неделя по умолчанию (Mon–Sun).
- `teacher_id`, `grade_id`, `subject_id` — `int`. **Комбинируются по И**.
- `ordering` — `start` (по умолчанию) или `-start`.
- `page`, `page_size` — пагинация DRF (дефолт `page_size` задаётся на сервере/в ручке).

**Сортировка**
- `ORDER BY start ASC, grade__name ASC` (стабильность при одинаковом времени начала).

**Ответ 200 (пагинированный)**
```json
{
  "count": 127,
  "next": "https://.../api/real_schedule/lessons/?page=2&from=2025-09-01&to=2025-09-30",
  "previous": null,
  "results": [
    {
      "id": 101,
      "subject": 5,
      "grade": 12,
      "teacher": 77,
      "date": "2025-09-01",
      "start_time": "09:15:00",
      "duration_minutes": 45,
      "type": "lesson",
      "room": null
    }
  ]
}
```

**Ошибки**: `400 INVALID_RANGE / RANGE_TOO_WIDE`, `401`, `403`.

---

## 👀 View as — «как видит пользователь» (новое)

### `GET /api/real_schedule/view_as/{user_id}/?from=&to=`

Отдаёт расписание **в том же контракте, что `/my/`**, но рассчитанное так, как его видит пользователь `user_id`.

**Доступ**
- `ADMIN`, `DIRECTOR`, `HEAD_TEACHER`, `METHODIST`, `AUDITOR` — любой `user_id`.
- `TEACHER` — только **своих учеников** (есть связь по занятиям в выбранном периоде).
- `PARENT` — только **своих детей**.
- Иные — `403`.

**Параметры (query)**: `from`, `to` — `YYYY-MM-DD`.

**Ответ 200**: формат **такой же, как у** `/my/` → `{from,to,count,results:[...]}`.

**Ошибки**: `400 INVALID_RANGE / RANGE_TOO_WIDE`, `401`, `403`, `404 NOT_FOUND`.

---

## 📄 Lesson detail (без изменений)

### `GET /api/real_schedule/lessons/<id>/`

Детальная карточка урока (поля урока, тема, участники, посещаемость).  
**Доступ** определяется ролевой логикой:
- админские роли — доступ ко всем,
- `TEACHER` — если назначен на урок,
- `STUDENT` — если подписан (по классу/индивидуально),
- `PARENT` — если его ребёнок подписан (по классу/индивидуально).

**Ответ 200 (пример, состав полей может отличаться)**
```json
{
  "id": 101,
  "subject": 5,
  "grade": 12,
  "teacher": 77,
  "date": "2025-09-01",
  "start_time": "10:00:00",
  "duration_minutes": 45,
  "type": "lesson",
  "room": null,
  "topic": "Натуральные числа",
  "students": [
    { "id": 501, "last_name": "Иванов", "first_name": "Пётр", "attended": true },
    { "id": 502, "last_name": "Сидорова", "first_name": "Анна", "attended": false }
  ]
}
```

**Ошибки**: `401`, `403`, `404`.

---

## ✅ Conduct lesson (без изменений)

### `POST /api/real_schedule/lessons/<id>/conduct/`

Помечает урок как проведённый; если привязан к КТП, заполняет `actual_date`, если оно пустое.

**Body (опц.)**
```json
{ "conducted_at": "2025-09-05T10:00:00Z" }
```

**Ответы**: `200 OK` (или `204 No Content`), ошибки `401/403/404`.

**Доступ**: только админские роли.

---

## ⚙️ Generate (без изменений)

### `POST /api/real_schedule/generate/`

Генерация реальных уроков за период.

**Параметры**
- `from`, `to` — `YYYY-MM-DD` (**обязательны**),
- `template_week_id` — id шаблонной недели,
- `rewrite_from` — дата, начиная с которой можно перезаписывать старые уроки (дефолт = `from`),
- `debug` — `true|false`.

**Успех 201 (пример)**
```json
{
  "version": "vX",
  "generation_batch_id": "batch-uuid",
  "deleted": 10,
  "created": 120,
  "created_with_ktp": 100,
  "created_without_ktp": 20,
  "warnings_count": 20,
  "warnings_summary": { "2/3": 5 }
}
```

**Ошибки**: `400 INVALID_RANGE / COLLISIONS`, `401`, `403`, `500`.

**Доступ**: админские роли.

---

## 🟣 Rooms (без изменений)

### `POST /api/real_schedule/rooms/get-or-create/`
Создаёт или возвращает комнату видеозанятия для урока.

**Body (пример)**
```json
{ "lesson_id": 101, "provider": "JITSI", "join_url": "https://meet.jit.si/..." }
```

### `POST /api/real_schedule/rooms/<id>/end/`
Завершает комнату (ставит `ended_at = now`).

**Ошибки**: `401`, `403`, `404`.

**Доступ**: админские роли.

---

## 🟪 Reference — справочники (минимум: учителя)

### `GET /api/reference/teachers/?q=ив&page=&page_size=`

Подстрочный поиск учителей (регистронезависимо). `q` — минимум **2 символа**.  
Возвращаются **атомарные поля** — фронт сам формирует отображаемую строку.

**Ответ 200 (пагинированный)**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    { "id": 77, "last_name": "Иванов", "first_name": "Иван", "middle_name": "Иванович" },
    { "id": 81, "last_name": "Ивлева", "first_name": "Анна", "middle_name": "Владимировна" }
  ]
}
```

**Ошибки**: `400 QUERY_TOO_SHORT`, `401`.

> По аналогии можно добавить: `/api/reference/grades/`, `/api/reference/subjects/`, `/api/reference/students/`, `/api/reference/parents/`.

---

## 🧪 Примеры проверок (smoke)

- `GET /api/real_schedule/lessons/?from=2025-09-01&to=2025-09-07` под **DIRECTOR** → **200**, пагинация и сортировка по возрастанию времени.
- `GET /api/real_schedule/view_as/{user_id}/?from=…&to=…`:
  - **TEACHER** → **200** для «своего» ученика, **403** для чужого,
  - **PARENT** → **200** для своего ребёнка, **403** для чужого,
  - **ADMIN** → **200** для любого.
- `GET /api/reference/teachers/?q=ив` → **200**; `q < 2` → **400**.

---

## 🧱 Заметки по производительности/безопасности

- **Индексы** в `RealLesson`: по времени старта и составные (`grade,start` / `teacher,start`) — ускоряют фильтрацию и сортировку.
- **Ограничение интервала** (≤ 31 день) предотвращает тяжёлые запросы.
- Новые ручки — **read-only** для `AUDITOR`/`METHODIST` (право видеть без редактирования).
- *(Опционально)* можно добавить **rate-limit** на справочники.

---

## Префикс и маршруты

Префикс модуля: `/api/real_schedule/`  

Ручки:
- `GET /api/real_schedule/my/`
- `GET /api/real_schedule/lessons/` *(новое)*
- `GET /api/real_schedule/view_as/{user_id}/` *(новое)*
- `GET /api/real_schedule/lessons/<id>/`
- `POST /api/real_schedule/lessons/<id>/conduct/`
- `POST /api/real_schedule/generate/`
- `POST /api/real_schedule/rooms/get-or-create/`
- `POST /api/real_schedule/rooms/<id>/end/`

Справочники:
- `GET /api/reference/teachers/` *(минимально реализовано)*
