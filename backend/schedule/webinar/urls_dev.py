from django.urls import path
from .views_dev import DevMakeDummyRecordingView

urlpatterns = [
    path("recordings/make-dummy/", DevMakeDummyRecordingView.as_view(), name="dev-make-dummy"),
]
