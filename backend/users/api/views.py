"""
REST API viewsets for user management.

This module contains API viewsets for retrieving and updating
user information through the REST API.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.mixins import UpdateModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from backend.users.models import User

from .serializers import CustomUserDetailsSerializer


class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    """
    ViewSet for user management in the REST API.

    This viewset provides endpoints for:
    - Retrieving user details (GET /api/users/{username}/)
    - Listing users (GET /api/users/)
    - Updating user information (PUT/PATCH /api/users/{username}/)
    - Getting current user info (GET /api/users/me/)

    Users can only access their own information for security.
    """

    # Serializer for user data
    serializer_class = CustomUserDetailsSerializer
    # Base queryset (filtered by get_queryset)
    queryset = User.objects.all()
    # Use username instead of pk for lookups
    lookup_field = "username"

    def get_queryset(self, *args, **kwargs):
        """
        Get queryset filtered to only include the current user.

        This ensures users can only access their own information
        through the API, providing security and privacy.

        Returns:
            QuerySet: Filtered queryset containing only the current user
        """
        assert isinstance(self.request.user.id, int)
        # Only return the current user's record
        return self.queryset.filter(id=self.request.user.id)

    @action(detail=False)
    def me(self, request):
        """
        Custom action to get the current user's information.

        This endpoint provides a convenient way to get the current
        user's details without needing to know their username.

        Endpoint: GET /api/users/me/

        Args:
            request: The HTTP request object

        Returns:
            Response: Serialized user data with 200 status
        """
        # Serialize the current user
        serializer = CustomUserDetailsSerializer(
            request.user,
            context={"request": request},
        )
        return Response(status=status.HTTP_200_OK, data=serializer.data)
