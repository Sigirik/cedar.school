# schedule/real_schedule/migrations/0004_populate_jitsi_room.py
from django.db import migrations
import uuid

def gen_name(room):
    base = f"lesson-{room.lesson_id}" if getattr(room, "lesson_id", None) else f"room-{room.id}"
    return f"cedar-{base}-{uuid.uuid4().hex[:6]}"

def forwards(apps, schema_editor):
    Room = apps.get_model("real_schedule", "Room")
    # Обновляем только те, где пусто или null
    for room in Room.objects.only("id", "lesson_id", "jitsi_room").all():
        if not getattr(room, "jitsi_room", None):
            room.jitsi_room = gen_name(room)
            room.save(update_fields=["jitsi_room"])

def backwards(apps, schema_editor):
    Room = apps.get_model("real_schedule", "Room")
    for room in Room.objects.only("id", "jitsi_room").all():
        if getattr(room, "jitsi_room", None):
            room.jitsi_room = None
            room.save(update_fields=["jitsi_room"])

class Migration(migrations.Migration):

    dependencies = [
        # ВАЖНО: имя ровно как сгенерировалось у тебя в 0003
        ("real_schedule", "0003_remove_room_provider_room_auto_manage_room_is_open_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
