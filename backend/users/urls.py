"""
URL configuration for user-related views.

This module defines URL patterns for user profile pages, including
detail views, update views, and redirect views.
"""
from django.urls import path

from .views import user_detail_view
from .views import user_redirect_view
from .views import user_update_view

# App name for namespacing URLs (e.g., users:detail)
app_name = "users"

# URL patterns for user views
urlpatterns = [
    # Redirect to current user's profile page
    # Uses ~ prefix to avoid conflicts with username patterns
    path("~redirect/", view=user_redirect_view, name="redirect"),
    # Update current user's profile
    # Uses ~ prefix to avoid conflicts with username patterns
    path("~update/", view=user_update_view, name="update"),
    # Display user profile by username
    # This must be last to avoid matching ~redirect or ~update
    path("<str:username>/", view=user_detail_view, name="detail"),
]
