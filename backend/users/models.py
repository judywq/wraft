import contextlib

from allauth.account.models import EmailAddress
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager
from django.db import transaction
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from backend.core.mixins import AccessControlManagerMixin
from backend.core.mixins import AccessControlMixin


class CustomUserManager(AccessControlManagerMixin, UserManager):
    pass


class User(AccessControlMixin, AbstractUser):
    """
    Default custom user model for MYAPP.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    objects = CustomUserManager()

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=False, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]

    required_fields = ["email", "name", "username"]

    def __str__(self):
        return f"{self.name} <{self.email}>"

    class Meta:
        permissions = [
            ("can_manage_limited_users", "Can manage users with limited visibility"),
        ]

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})

    def save(self, *args, **kwargs):
        """Override save to sync email with EmailAddress."""
        email_changed = False
        if self.pk:  # If this is an existing user
            with contextlib.suppress(User.DoesNotExist):
                old_user = User.objects.get(pk=self.pk)
                if old_user.email != self.email:
                    email_changed = True

        with transaction.atomic():
            super().save(*args, **kwargs)

            if email_changed:
                # Update or create primary email address
                EmailAddress.objects.update_or_create(
                    user=self,
                    primary=True,
                    defaults={
                        "email": self.email,
                        "verified": True,  # Set new email to verified
                    },
                )
                # Delete any other email addresses for this user
                EmailAddress.objects.filter(user=self).exclude(
                    email=self.email,
                ).delete()
