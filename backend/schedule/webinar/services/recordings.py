import os
import tempfile
import requests
from datetime import timezone
from django.db import transaction
from django.utils.timezone import now

from schedule.real_schedule.models import Room  # путь к вашей модели
from schedule.webinar.storage import get_storage

def _dst_path_for_room(room: Room, ext: str = "mp4") -> str:
    # lessons/456/2025-09-08T08-00-00Z.mp4
    start = (room.scheduled_start or now()).astimezone(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    base = f"lessons/{room.lesson_id or room.id}/{start}.{ext}"
    return base

@transaction.atomic
def recording_uploaded_from_jaas(room_id: int, preauth_link: str, file_ext: str = "mp4") -> Room:
    room = Room.objects.select_for_update().get(id=room_id)
    storage = get_storage()

    with requests.get(preauth_link, stream=True, timeout=300) as r:
        r.raise_for_status()
        with tempfile.TemporaryFile() as tmp:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    tmp.write(chunk)
            tmp.seek(0)
            dst_rel = _dst_path_for_room(room, ext=file_ext)
            saved = storage.save_fileobj(tmp, dst_rel)

    room.recording_status = "READY"
    room.recording_file_url = saved.public_url
    room.recording_ended_at = room.recording_ended_at or now()
    room.save(update_fields=["recording_status", "recording_file_url", "recording_ended_at"])
    return room

@transaction.atomic
def recording_uploaded_from_jibri(room_id: int, local_path: str, file_ext: str | None = None) -> Room:
    room = Room.objects.select_for_update().get(id=room_id)
    storage = get_storage()

    ext = file_ext or os.path.splitext(local_path)[1].lstrip(".") or "mp4"
    dst_rel = _dst_path_for_room(room, ext=ext)
    saved = storage.save_local_path(local_path, dst_rel)

    room.recording_status = "READY"
    room.recording_file_url = saved.public_url
    room.recording_ended_at = room.recording_ended_at or now()
    room.save(update_fields=["recording_status", "recording_file_url", "recording_ended_at"])
    return room
