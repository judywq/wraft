"""
User-related views for public-facing pages.

This module contains views for displaying and updating user profiles,
including detail views, update views, and redirect views.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView

from backend.users.models import User


class UserDetailView(LoginRequiredMixin, DetailView):
    """
    View for displaying a user's profile page.

    This view shows the public profile of a user identified by username.
    Requires the user to be logged in to view profiles.
    """

    model = User
    # Field to use for lookup (username instead of pk)
    slug_field = "username"
    # URL parameter name for the username
    slug_url_kwarg = "username"


# View function for URL routing
user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    View for updating the current user's profile.

    This view allows users to update their own profile information.
    Users can only edit their own profile, not other users' profiles.
    """

    model = User
    # Fields that can be edited by the user
    fields = ["name"]
    # Success message displayed after successful update
    success_message = _("Information successfully updated")

    def get_success_url(self) -> str:
        """
        Get the URL to redirect to after successful update.

        Returns:
            str: URL of the user's detail page
        """
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None = None) -> User:
        """
        Get the user object to edit.

        Always returns the currently logged-in user, ensuring users
        can only edit their own profile.

        Args:
            queryset: Optional queryset (not used, always returns request.user)

        Returns:
            User: The current user instance
        """
        assert self.request.user.is_authenticated  # type guard
        return self.request.user


# View function for URL routing
user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    """
    View that redirects to the current user's profile page.

    This view is useful for redirecting users to their own profile
    after login or from a generic user URL.
    """

    # Use temporary redirect (302) instead of permanent (301)
    permanent = False

    def get_redirect_url(self) -> str:
        """
        Get the URL to redirect to.

        Returns:
            str: URL of the current user's detail page
        """
        return reverse("users:detail", kwargs={"username": self.request.user.username})


# View function for URL routing
user_redirect_view = UserRedirectView.as_view()
