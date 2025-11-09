"""
User model and related components.

This module defines the custom User model for the application,
including access control functionality and email synchronization.
"""
import contextlib

from allauth.account.models import EmailAddress
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager
from django.db import transaction
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from backend.common.mixins import AccessControlManagerMixin
from backend.common.mixins import AccessControlMixin


class CustomUserManager(AccessControlManagerMixin, UserManager):
    """
    Custom user manager with access control functionality.

    This manager extends Django's UserManager with access control methods
    from AccessControlManagerMixin, allowing filtering of users based on
    creator relationships and permissions.
    """

    pass


class User(AccessControlMixin, AbstractUser):
    """
    Default custom user model for MYAPP.

    This model extends Django's AbstractUser with:
    - A single 'name' field instead of first_name/last_name
    - Access control based on created_by field
    - Automatic email synchronization with django-allauth

    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # Custom manager with access control methods
    objects = CustomUserManager()

    # Single name field instead of first_name/last_name
    # This covers name patterns around the globe better
    name = CharField(_("Name of User"), blank=False, max_length=255)
    # Disable first_name and last_name fields
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]

    # Fields required for user creation
    required_fields = ["email", "name", "username"]

    def __str__(self):
        """
        String representation of the user.

        Returns:
            str: User's name and email in format "Name <email>"
        """
        return f"{self.name} <{self.email}>"

    class Meta:
        # Custom permissions for user management
        permissions = [
            ("can_manage_limited_users", "Can manage users with limited visibility"),
        ]

    def get_absolute_url(self) -> str:
        """
        Get URL for user's detail view.

        Returns:
            str: URL for user detail page
        """
        return reverse("users:detail", kwargs={"username": self.username})

    def save(self, *args, **kwargs):
        """
        Override save to sync email with EmailAddress model.

        When a user's email is changed, this method:
        1. Updates or creates the primary EmailAddress record
        2. Deletes any other email addresses for this user
        3. Marks the new email as verified

        This ensures django-allauth's EmailAddress model stays in sync
        with the User model's email field.

        Args:
            *args: Positional arguments passed to parent save method
            **kwargs: Keyword arguments passed to parent save method
        """
        email_changed = False
        # Check if email changed for existing users
        if self.pk:  # If this is an existing user
            with contextlib.suppress(User.DoesNotExist):
                old_user = User.objects.get(pk=self.pk)
                if old_user.email != self.email:
                    email_changed = True

        # Use transaction to ensure atomicity
        with transaction.atomic():
            # Save the user instance
            super().save(*args, **kwargs)

            # Sync email with django-allauth's EmailAddress model
            if email_changed:
                # Update or create primary email address
                # This ensures django-allauth knows about the email change
                EmailAddress.objects.update_or_create(
                    user=self,
                    primary=True,
                    defaults={
                        "email": self.email,
                        "verified": True,  # Set new email to verified
                    },
                )
                # Delete any other email addresses for this user
                # This prevents duplicate email records
                EmailAddress.objects.filter(user=self).exclude(
                    email=self.email,
                ).delete()
