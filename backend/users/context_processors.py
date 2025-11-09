"""
Context processors for user-related template context.

This module provides context processors that add variables to
all template contexts, making them available in all templates.
"""
from django.conf import settings


def allauth_settings(request):
    """
    Expose django-allauth settings in templates.

    This context processor makes django-allauth settings available
    in all templates, allowing templates to check if registration
    is enabled, etc.

    Args:
        request: The HTTP request object

    Returns:
        dict: Dictionary of settings to add to template context
    """
    return {
        # Whether user registration is allowed
        "ACCOUNT_ALLOW_REGISTRATION": settings.ACCOUNT_ALLOW_REGISTRATION,
    }
