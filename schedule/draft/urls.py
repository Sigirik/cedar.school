"""
Маршруты для работы с единственным черновиком.
"""

from django.urls import path
from .views import active_draft, commit_active_draft

urlpatterns = [
    path('active/', active_draft, name='active-draft'),              # GET, PATCH, POST
    path('active/commit/', commit_active_draft, name='commit-draft'),  # POST
]

