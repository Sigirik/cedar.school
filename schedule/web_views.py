from django.shortcuts import render, redirect
from .models import RealLesson, TemplateLesson
from .forms import TemplateLessonForm, RealLessonForm
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_GET


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


def real_lesson_list_view(request):
    lessons = RealLesson.objects.order_by('date', 'start_time')
    return render(request, 'schedule/real_lesson_list.html', {
        'lessons': lessons
    })


def real_lesson_create_view(request):
    form = RealLessonForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect('real_lesson_list')
    return render(request, 'schedule/real_lesson_form.html', {'form': form})


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