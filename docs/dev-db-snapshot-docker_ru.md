# Cedar.school — Экспорт/импорт dev‑базы через Docker

Ниже — короткая инструкция, как **снимать снапшот** (зерно) текущей SQLite‑БД и как **восстанавливать** базу из снапшота. Команды выполняются из **корня репозитория**.

---

## Экспорт (создать/обновить снапшот)

```powershell
# (1) Разрешить запуск скриптов в текущей сессии
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# (2) (опц.) Санитизировать БД перед экспортом (пароли/почты)
docker compose exec backend bash -lc "python manage.py sanitize_for_snapshot --password pass12345"

# (3) Экспорт снапшота (остановит backend, скопирует БД, запустит обратно)
.ackend\scripts\db-export.ps1 -Docker

# или с кастомным именем файла:
.ackend\scripts\db-export.ps1 -Docker -SnapshotPath "seeds/cedar_2025-09-05.sqlite3"
```

---

## Импорт (восстановить базу из снапшота)

```powershell
# Разрешить запуск скриптов в текущей сессии
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Базовый случай (по умолчанию берётся seeds/cedar_dev.sqlite3)
.ackend\scripts\db-import.ps1 -Docker

# Если используешь другой снимок:
.ackend\scripts\db-import.ps1 -Docker -SnapshotPath "seeds/cedar_2025-09-05.sqlite3"

# Если точно не хочешь гонять миграции после импорта:
.ackend\scripts\db-import.ps1 -Docker -SkipMigrate
```

---

### Примечания
- Скрипты останавливают/запускают сервис `backend` в Docker при необходимости.
- После импорта проверь логи: `docker compose logs -f backend` и открой `http://localhost:8000/admin`.
- Снимки хранятся в папке `seeds/` (рекомендуется трекать их через **Git LFS**).
