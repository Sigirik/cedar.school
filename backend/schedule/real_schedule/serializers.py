import datetime as dt
from rest_framework import serializers
from schedule.real_schedule.models import RealLesson, Room

class _RefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()

class _TeacherRefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    fio = serializers.CharField()

class _LessonTypeRefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    key = serializers.CharField()
    label = serializers.CharField()

class RealLessonSerializer(serializers.ModelSerializer):
    end = serializers.SerializerMethodField()
    subject = _RefSerializer(source="subject")
    grade   = _RefSerializer(source="grade")
    teacher = serializers.SerializerMethodField()
    lesson_type = _LessonTypeRefSerializer(source="lesson_type")

    class Meta:
        model = RealLesson
        fields = (
            "id", "subject", "grade", "teacher",
            "start", "duration_minutes", "end",
            "lesson_type", "topic_order", "topic_title", "ktp_entry",
            "source", "template_week_id", "template_lesson_id",
            "generation_batch_id", "version", "conducted_at",
        )

    def get_end(self, obj):
        return (obj.start + dt.timedelta(minutes=obj.duration_minutes)).isoformat().replace("+00:00", "Z")

    def get_teacher(self, obj):
        # если у User есть свойство short_fio — используем; иначе username/фамилия
        fio = getattr(obj.teacher, "short_fio", None) or getattr(obj.teacher, "username", str(obj.teacher))
        return {"id": obj.teacher_id, "fio": fio}


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ("id", "lesson", "provider", "join_url", "started_at", "ended_at")
        read_only_fields = ("started_at", "ended_at")
