from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from schedule.real_schedule.models import Room

@receiver(post_save, sender=Room)
def on_room_saved(sender, instance: Room, created, **kwargs):
    # Если вебинар завершён — фиксируем факт проведения
    if instance.ended_at:
        lesson = instance.lesson
        if not lesson.conducted_at:
            lesson.conducted_at = instance.ended_at
            lesson.save(update_fields=["conducted_at", "updated_at"])
            # Проставляем факт в КТП
            if lesson.ktp_entry_id:
                # actual_date — дата без времени
                from schedule.ktp.models import KTPEntry
                KTPEntry.objects.filter(id=lesson.ktp_entry_id, actual_date__isnull=True)\
                                .update(actual_date=instance.ended_at.date())
