from django.shortcuts import render, redirect
from .models import RealLesson, TemplateWeek, TemplateLesson
from .forms import TemplateLessonForm
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import TemplateWeekDetailSerializer

def template_week_view(request):
    lessons = TemplateLesson.objects.all()
    form = TemplateLessonForm()

    if request.method == 'POST':
        form = TemplateLessonForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('template_week')

    return render(request, 'schedule/template_week.html', {
        'form': form,
        'lessons': lessons
    })


from .models import RealLesson

def real_lesson_list_view(request):
    lessons = RealLesson.objects.order_by('date', 'start_time')
    return render(request, 'schedule/real_lesson_list.html', {
        'lessons': lessons
    })

from django.shortcuts import render, redirect
from .forms import RealLessonForm

def real_lesson_create_view(request):
    form = RealLessonForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect('real_lesson_list')  # или другой маршрут
    return render(request, 'schedule/real_lesson_form.html', {'form': form})

from django.http import JsonResponse, Http404
from django.views.decorators.http import require_GET
from .models import TemplateLesson

@require_GET
def template_lesson_detail_json(request, pk):
    try:
        lesson = TemplateLesson.objects.get(pk=pk)
    except TemplateLesson.DoesNotExist:
        raise Http404("Шаблон не найден")

    data = {
        "subject": lesson.subject.id,
        "teacher": lesson.teacher.id,
        "grade": lesson.grade.id,
        "start_time": lesson.start_time.strftime("%H:%M"),
        "duration_minutes": lesson.duration_minutes,
    }
    return JsonResponse(data)

class ActiveTemplateWeekView(APIView):
    def get(self, request):
        active_week = TemplateWeek.objects.filter(is_active=True).order_by("-created_at").first()
        if not active_week:
            return Response({"detail": "No active template week found."}, status=404)
        data = TemplateWeekDetailSerializer(active_week).data
        return Response(data)

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import TemplateWeek, TemplateLesson
from .serializers import TemplateWeekSerializer

class TemplateWeekViewSet(viewsets.ModelViewSet):
    queryset = TemplateWeek.objects.all()
    serializer_class = TemplateWeekSerializer

    @action(detail=False, methods=['get'])
    def historical_templates(self, request):
        templates = TemplateWeek.objects.filter(is_draft=False).order_by('-created_at')
        serializer = self.get_serializer(templates, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def clone_to_draft(self, request, pk=None):
        source_week = self.get_object()

        # Удаляем существующий черновик, если force=true
        force = request.data.get("force", False)
        existing_draft = TemplateWeek.objects.filter(is_draft=True, school_year=source_week.school_year).first()
        if existing_draft:
            if not force:
                return Response({"detail": "draft_exists"}, status=status.HTTP_409_CONFLICT)
            TemplateLesson.objects.filter(template_week=existing_draft).delete()
            draft = existing_draft
        else:
            draft = TemplateWeek.objects.create(
                school_year=source_week.school_year,
                is_draft=True,
                name=f"Черновик из {source_week.name}"
            )

        # Копируем уроки
        lessons = TemplateLesson.objects.filter(template_week=source_week)
        for lesson in lessons:
            lesson.pk = None
            lesson.template_week = draft
            lesson.save()

        return Response(TemplateWeekSerializer(draft).data, status=status.HTTP_201_CREATED)

