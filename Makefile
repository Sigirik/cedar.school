# Makefile
DC ?= docker compose

.PHONY: up down logs migrate makemigrations createsuperuser shell test rebuild

up:
	$(DC) up -d --build

down:
	$(DC) down

logs:
	$(DC) logs -f web db

rebuild:
	$(DC) build --no-cache web

migrate:
	$(DC) exec web python manage.py migrate

makemigrations:
	$(DC) exec web python manage.py makemigrations

createsuperuser:
	$(DC) exec web python manage.py createsuperuser

shell:
	$(DC) exec web python manage.py shell

test:
	# Если используете pytest: замените на `pytest`
	$(DC) exec web python manage.py test
