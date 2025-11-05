from django.urls import path

from .views import ActiveModelsView

urlpatterns = [
    path("llm-models/", ActiveModelsView.as_view(), name="active-models"),
]
