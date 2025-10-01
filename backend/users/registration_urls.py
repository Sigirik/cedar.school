# users/registration_urls.py
from django.urls import path
from users.views import CsrfExemptRegisterView

urlpatterns = [
    path("users/", CsrfExemptRegisterView.as_view(), name="csrf-exempt-register"),
]