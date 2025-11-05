import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import EssayEvaluation
from .serializers import BriefEssayEvaluationSerializer
from .serializers import EssayEvaluationCreateSerializer
from .serializers import EssayEvaluationRetrieveSerializer
from .tasks import process_essay_evaluation

logger = logging.getLogger(__name__)

User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class EssayEvaluationViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing essay evaluations.
    """

    permission_classes = [IsAuthenticated]
    queryset = EssayEvaluation.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action == "list":
            return BriefEssayEvaluationSerializer
        if self.action == "create":
            return EssayEvaluationCreateSerializer
        return EssayEvaluationRetrieveSerializer

    def get_queryset(self):
        return EssayEvaluation.objects.filter(created_by=self.request.user)

    @transaction.non_atomic_requests
    def create(self, request, *args, **kwargs):
        """
        Create a new essay evaluation and process it in the background.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not EssayEvaluation.check_quota(request.user):
            return Response(
                {"error": "Daily quota exceeded, please try again tomorrow."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Create the essay evaluation record
        essay_evaluation = EssayEvaluation.objects.create(
            essay_prompt=serializer.validated_data["essay_prompt"],
            essay_text=serializer.validated_data["essay_text"],
            created_by=request.user,
            status=EssayEvaluation.Status.PENDING,
        )

        # Start background processing
        process_essay_evaluation.delay(essay_evaluation.id)

        return Response(
            {
                "id": essay_evaluation.id,
            },
            status=status.HTTP_202_ACCEPTED,
        )
