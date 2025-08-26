# backend/Dockerfile
FROM python:3.12-slim

# Чуть ускоряем интерпретатор и вывод логов
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Системные зависимости (для psycopg/psycopg2 и сборки колёс)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl bash \
 && rm -rf /var/lib/apt/lists/*

# Каталог приложения внутри контейнера
WORKDIR /app

# Ставим зависимости (слой кэшируется)
COPY requirements.txt /app/

# Позволим переопределять индекс (если нужно) и усилим pip
ARG PIP_INDEX_URL=https://pypi.org/simple
ENV PIP_INDEX_URL=${PIP_INDEX_URL}

RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir --default-timeout=120 --retries 5 -r requirements.txt

# Копируем весь backend (включая seed и scripts)
COPY . /app/

# Порт dev-сервера Django
EXPOSE 8000

# Запускаем через entrypoint (по умолчанию из scripts/entrypoint.sh)
CMD ["bash", "scripts/entrypoint.sh"]
