# backend/schedule/webinar/management/commands/webinar_maintain.py
from django.core.management.base import BaseCommand

from schedule.webinar.services.auto import (
    maintain_rooms,
    precreate_rooms_for_open_lessons,
)

class Command(BaseCommand):
    help = "Создаёт/закрывает вебинарные комнаты по расписанию. Запускать периодически."

    def add_arguments(self, parser):
        parser.add_argument("--ahead", type=int, default=48,
                            help="На сколько часов вперёд готовить комнаты для открытых уроков (default: 48)")
        parser.add_argument("--once", action="store_true",
                            help="Выполнить один цикл и выйти")

    def handle(self, *args, **opts):
        created, closed = maintain_rooms()
        precreated = precreate_rooms_for_open_lessons(hours_ahead=opts["ahead"])
        self.stdout.write(
            self.style.SUCCESS(
                f"webinar_maintain: created={created}, closed={closed}, precreated_open={precreated}"
            )
        )
