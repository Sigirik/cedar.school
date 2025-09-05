# Cedar.school API — КТП (Календарно‑тематический план)

Эндпоинты для работы с КТП: шаблоны, разделы, уроки (entries).

---

## 📑 Templates (KTPTemplate)

### GET /api/ktp/ktptemplate/
Список всех КТП-шаблонов【88†source】.

### POST /api/ktp/ktptemplate/
Создать новый КТП-шаблон.  
**Body пример:**
```json
{
  "name": "КТП 5А Математика",
  "subject": 10,
  "grade": 5
}
```

---

## 📂 Sections (KTPSection)

### GET /api/ktp/ktpsection/
Список разделов КТП【88†source】.

### POST /api/ktp/ktpsection/
Создать новый раздел КТП.  
**Body пример:**
```json
{
  "template": 1,
  "title": "Раздел 1"
}
```

---

## 📘 Entries (KTPEntry)

### GET /api/ktp/ktpentry/
Список всех уроков КТП (entries)【88†source】.

### POST /api/ktp/ktpentry/
Создать новую запись (урок) КТП.  
**Body пример:**
```json
{
  "section": 1,
  "lesson_number": 1,
  "topic": "Введение"
}
```

---

## ⚙️ Использование

- Все запросы требуют `Authorization: Bearer {{access_token}}`.  
- Для создания указывайте корректные id связных моделей (`subject`, `grade`, `template`, `section`).  
- CRUD (GET/POST/PATCH/DELETE) поддерживается у всех трёх ViewSet’ов: Template, Section, Entry.

