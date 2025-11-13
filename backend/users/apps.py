"""
Django app configuration for users app.

This module configures the users app and imports signal handlers
when the app is ready.
"""
import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    """
    App configuration for the users app.

    This configuration class sets up the users app and imports
    signal handlers when Django is ready.
    """

    # App name matching the package path
    name = "backend.users"
    # Human-readable name for the app
    verbose_name = _("Users")

    def ready(self):
        """
        Called when Django is ready.

        This method is called after Django has loaded all apps.
        It imports signal handlers if they exist.
        """
        # Import signals if they exist (suppress ImportError if not)
        with contextlib.suppress(ImportError):
            import backend.users.signals  # noqa: F401
