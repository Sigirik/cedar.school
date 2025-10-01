from django.urls import path
from .views import TeacherRefView, GradeRefView, SubjectRefView, StudentRefView, ParentRefView

urlpatterns = [
    path("teachers/", TeacherRefView.as_view()),
    path("grades/",   GradeRefView.as_view()),
    path("subjects/", SubjectRefView.as_view()),
    path("students/", StudentRefView.as_view()),
    path("parents/",  ParentRefView.as_view()),
]