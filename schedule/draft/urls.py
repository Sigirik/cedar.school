"""
Маршруты для работы с единственным черновиком.
"""

from django.urls import path
from .views import (
    get_or_create_draft,
    create_draft_from_template,
    create_empty_draft,
    update_draft,
    commit_draft,
)

urlpatterns = [
    path('template-drafts/', get_or_create_draft, name='get-or-create-draft'),  # GET — получить, POST — создать на основе активной/по id (по желанию)
    path('template-drafts/create-from/', create_draft_from_template, name='create-draft-from-template'),  # POST с template_id (или без — с активной)
    path('template-drafts/create-empty/', create_empty_draft, name='create-empty-draft'),  # POST
    path('template-drafts/update/', update_draft, name='update-draft'),  # PATCH
    path('template-drafts/commit/', commit_draft, name='commit-draft'),  # POST
]
