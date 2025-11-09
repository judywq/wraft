"""
Django REST Framework views for essay evaluation API.

This module provides API endpoints for creating and retrieving essay
evaluations. Includes pagination, authentication, and limit checking.
"""

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

UserModel = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    """
    Pagination configuration for essay evaluation list views.

    Default page size is 10, with configurable page size up to 100.
    """
    page_size = 10  # Default number of items per page
    page_size_query_param = "page_size"  # Query parameter to override page size
    max_page_size = 100  # Maximum allowed page size


class EssayEvaluationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing essay evaluations.

    Provides CRUD operations for essay evaluations. Users can only
    access their own evaluations. Creating an evaluation triggers
    background processing via Celery.
    """

    permission_classes = [IsAuthenticated]  # Require authentication
    queryset = EssayEvaluation.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the action.

        Uses different serializers for different actions:
        - list: BriefEssayEvaluationSerializer (minimal fields)
        - create: EssayEvaluationCreateSerializer (input fields only)
        - retrieve: EssayEvaluationRetrieveSerializer (full data)

        Returns:
            Serializer class appropriate for the current action
        """
        if self.action == "list":
            return BriefEssayEvaluationSerializer
        if self.action == "create":
            return EssayEvaluationCreateSerializer
        return EssayEvaluationRetrieveSerializer

    def get_queryset(self):
        """
        Filter queryset to only include evaluations created by the current user.

        Ensures users can only see their own evaluations for privacy.

        Returns:
            QuerySet: Filtered queryset of user's evaluations
        """
        return EssayEvaluation.objects.filter(created_by=self.request.user)

    @transaction.non_atomic_requests
    def create(self, request, *args, **kwargs):
        """
        Create a new essay evaluation and initiate background processing.

        Validates the input data, checks daily limits, creates the evaluation
        record, and starts background processing via Celery. Returns 202
        Accepted status as processing happens asynchronously.

        Args:
            request: The HTTP request object

        Returns:
            Response: HTTP 202 Accepted with evaluation ID, or 429 if limit exceeded

        Raises:
            ValidationError: If input data is invalid
        """
        # Validate input data
        request_serializer = self.get_serializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        # Check if user has exceeded daily limit
        if EssayEvaluation.is_limit_exceeded(request.user):
            return Response(
                {"error": "Daily limit exceeded, please try again tomorrow."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Create the evaluation record with PENDING status
        evaluation_record = EssayEvaluation.objects.create(
            essay_prompt=request_serializer.validated_data["essay_prompt"],
            essay_text=request_serializer.validated_data["essay_text"],
            created_by=request.user,
            status=EssayEvaluation.Status.PENDING,
        )

        # Initiate background processing via Celery
        # Processing happens asynchronously (surface correction, scoring, etc.)
        process_essay_evaluation.delay(evaluation_record.id)

        # Return 202 Accepted with evaluation ID
        # Client can poll for status or wait for completion
        return Response(
            {
                "id": evaluation_record.id,
            },
            status=status.HTTP_202_ACCEPTED,
        )
