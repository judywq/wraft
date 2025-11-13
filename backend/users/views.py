"""
DRF viewset for read/list/update of the *current* user,
plus a convenience /me endpoint.
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin, UpdateModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from backend.users.models import User
from .serializers import CustomUserDetailsSerializer


class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    """
    Endpoints:
      - GET    /api/users/            -> list (current user only)
      - GET    /api/users/{username}/ -> retrieve (current user only)
      - PATCH  /api/users/{username}/ -> partial update (current user only)
      - PUT    /api/users/{username}/ -> update (current user only)
      - GET    /api/users/me/         -> current user snapshot
    """

    serializer_class = CustomUserDetailsSerializer
    queryset = User.objects.all()
    lookup_field = "username"

    # Only ever expose the authenticated user's own record
    def get_queryset(self, *args, **kwargs):
        user = getattr(self.request, "user", None)
        # retain the same safety check intent while avoiding hard assertions
        if not user or not isinstance(getattr(user, "id", None), int):
            return self.queryset.none()
        return self.queryset.filter(id=user.id)

    def get_serializer_context(self):
        # Make sure nested serializers have request available
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    @action(detail=False, methods=["GET"])
    def me(self, request):
        """
        Shortcut for the current user's own details.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
