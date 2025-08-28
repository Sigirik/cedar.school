FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# + postgresql-client (даёт psql/pg_isready)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev postgresql-client curl bash \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir --default-timeout=120 --retries 5 -r requirements.txt

# Копируем весь backend (включая scripts/entrypoint.sh)
COPY . /app/

EXPOSE 8000

# ВАЖНО: один способ запуска — наш скрипт в репозитории
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
