from django.shortcuts import render, redirect
from .models import TemplateWeek, TemplateLesson
from .forms import TemplateLessonForm

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