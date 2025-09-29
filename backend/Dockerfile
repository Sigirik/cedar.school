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

# Копируем код приложения
COPY . /app/

# гарантируем, что есть pg_isready
RUN apt-get update \
 && apt-get install -y --no-install-recommends postgresql-client \
 && rm -rf /var/lib/apt/lists/*


# Копируем entrypoint туда, где его не накроет volume
COPY scripts/entrypoint.sh /usr/local/bin/cedar-entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/cedar-entrypoint.sh \
 && chmod +x /usr/local/bin/cedar-entrypoint.sh

# удобные дефолтные переменные
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# запускаем через entrypoint и передаём команду (dev — runserver)
ENTRYPOINT ["/usr/local/bin/cedar-entrypoint.sh"]
CMD ["python","manage.py","runserver","0.0.0.0:8000","--insecure"]

RUN find /app/scripts -type f -name "*.sh" -exec sed -i 's/\r$//' {} \; \
    && chmod +x /app/scripts/*.sh

EXPOSE 8000

# ВАЖНО: один способ запуска — наш скрипт в репозитории
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
