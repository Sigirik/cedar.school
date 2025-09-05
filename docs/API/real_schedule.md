# Cedar.school API — Real Schedule

Эндпоинты реального расписания: «моё расписание», генерация, проведение урока, комнаты видеозанятий.

---

## 👤 My schedule

### GET /api/real_schedule/my/?from=&to=
Возвращает расписание **для текущего пользователя** за период. 
Если from/to не указаны — используется неделя по умолчанию. 
Ролевая логика: админ-ролии видят всё; учитель — свои занятия; ученик — по классу/индивидуалкам; родитель — агрегированно по детям (опц. `children=1,2`)【103†source】.

**Ответ:**
```json
{ "from": "YYYY-MM-DD", "to": "YYYY-MM-DD", "count": N, "results": [ ... ] }
```

---

## ⚙️ Generate

### POST /api/real_schedule/generate/
Генерирует реальные занятия за период. 
Параметры можно передать в теле или как query:
- `from` (YYYY-MM-DD), `to` (YYYY-MM-DD) — обязательные, корректный интервал.
- `template_week_id` — использовать конкретную шаблонную неделю (иначе выбор внутри сервиса).
- `rewrite_from` — дата, с которой перезаписывать старые уроки (по умолчанию = `from`).
- `debug` — bool.
 
**Успех (201)**
```json
{
  "version": "vX",
  "generation_batch_id": "...",
  "deleted": 10,
  "created": 120,
  "created_with_ktp": 100,
  "created_without_ktp": 20,
  "warnings_count": 20,
  "warnings_summary": {"2/3": 5},
  "warnings": [ {"message": "Нет KTPEntry для 2025-09-01 2/3"} ]
}
```
**Ошибки:** 400 `INVALID_RANGE` / `COLLISIONS`, 500 `INTERNAL_ERROR`.  
**Роли:** по коду — админские (IsAdminUser в комментах)【102†source】.

---

## ✅ Conduct Lesson

### POST /api/real_schedule/lessons/<id>/conduct/
Помечает урок как проведённый; если привязан к КТП, выставляет `actual_date` (если не было).  
Body опц.: `{ "conducted_at": "2025-09-05T10:00:00Z" }`.  
**Роли:** IsAdminUser (по коду)【102†source】.

---

## 🟣 Rooms

### POST /api/real_schedule/rooms/get-or-create/
Создать/вернуть комнату видеозанятия. Тело: `{ "lesson_id": <int>, "provider": "JITSI", "join_url": "<url>" }`.  
Обязательны `lesson_id` и `join_url`. Возвращает Room.  
**Роли:** IsAdminUser【102†source】.

### POST /api/real_schedule/rooms/<id>/end/
Завершить комнату (`ended_at = now`), вернуть Room.  
**Роли:** IsAdminUser【102†source】.

---

## 🧭 Роутинг
Префикс модуля: `/api/real_schedule/`  
Пути: `my/`, `generate/`, `lessons/<id>/conduct/`, `rooms/get-or-create/`, `rooms/<id>/end/`【101†source】.

---

## 🔐 Авторизация
Все запросы выполняются с `Authorization: Bearer {{access_token}}`.
