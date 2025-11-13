from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import EssayEvaluationViewSet

router = DefaultRouter()
router.register(r"evaluate-essay", EssayEvaluationViewSet, basename="essay-evaluation")

urlpatterns = [
    path("", include(router.urls)),
]
