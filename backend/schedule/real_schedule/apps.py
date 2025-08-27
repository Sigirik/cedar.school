from django.apps import AppConfig

class RealScheduleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "schedule.real_schedule"

    def ready(self):
        from . import signals  # noqa
