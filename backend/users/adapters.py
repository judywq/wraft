"""
Django-allauth adapters for account and social account management.

This module provides custom adapters for django-allauth to control
registration behavior and populate user data from social providers.
"""
from __future__ import annotations

import typing

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings

if typing.TYPE_CHECKING:
    from allauth.socialaccount.models import SocialLogin
    from django.http import HttpRequest

    from backend.users.models import User


class AccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter for django-allauth.

    This adapter controls account-related behavior such as whether
    registration is open for standard email/password signups.
    """

    def is_open_for_signup(self, request: HttpRequest) -> bool:
        """
        Check if registration is open for standard account signup.

        Args:
            request: The HTTP request object

        Returns:
            bool: True if registration is allowed, False otherwise
        """
        registration_enabled = getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)
        return registration_enabled


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter for django-allauth.

    This adapter controls social account-related behavior such as
    whether registration is open for OAuth signups and how user
    data is populated from social providers.
    """

    def is_open_for_signup(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
    ) -> bool:
        """
        Check if registration is open for social account signup.

        Args:
            request: The HTTP request object
            sociallogin: The social login object from the provider

        Returns:
            bool: True if registration is allowed, False otherwise
        """
        registration_allowed = getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)
        return registration_allowed

    def populate_user(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
        data: dict[str, typing.Any],
    ) -> User:
        """
        Populate user information from social provider data.

        This method extracts user information from OAuth provider data
        and populates the User model. It handles the 'name' field by
        combining first_name and last_name if a full name is not provided.

        See: https://docs.allauth.org/en/latest/socialaccount/advanced.html#creating-and-populating-user-instances

        Args:
            request: The HTTP request object
            sociallogin: The social login object from the provider
            data: Dictionary containing user data from the provider

        Returns:
            User: The populated user instance
        """
        # Call parent method to populate standard fields
        user_instance = super().populate_user(request, sociallogin, data)

        # Populate name field if not already set
        if not user_instance.name:
            full_name = data.get("name")
            if full_name:
                user_instance.name = full_name
            else:
                # Fall back to combining first_name and last_name
                given_name = data.get("first_name")
                family_name = data.get("last_name")
                if given_name:
                    user_instance.name = given_name
                    if family_name:
                        user_instance.name = f"{given_name} {family_name}"

        return user_instance
