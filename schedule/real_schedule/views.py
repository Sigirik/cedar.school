from rest_framework import viewsets
from .models import RealLesson
from .serializers import RealLessonSerializer

class RealLessonViewSet(viewsets.ModelViewSet):
    queryset = RealLesson.objects.all()
    serializer_class = RealLessonSerializer
