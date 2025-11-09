"""
User-related forms for admin interface and authentication.

This module contains forms for user creation, registration, and bulk import
functionality. It includes forms for Django admin, django-allauth signup,
and Excel-based user import.
"""
import io

import pandas as pd
from allauth.account.forms import SignupForm
from allauth.account.models import EmailAddress
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django import forms
from django.contrib.auth import forms as admin_forms
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .models import User


class CourseLimitingFormMixin:
    """
    Mixin to limit course choices based on user access.

    This mixin stores the staff user who is creating/editing the form,
    which can be used to limit course choices based on permissions.
    """

    def __init__(self, *args, **kwargs):
        # Extract staff_user from kwargs to pass to form initialization
        # This allows forms to know which admin user is performing the action
        self.staff_user = kwargs.pop("staff_user", None)
        super().__init__(*args, **kwargs)


class UserAdminChangeForm(CourseLimitingFormMixin, admin_forms.UserChangeForm):
    """
    Form for editing existing users in the Django admin interface.

    Extends the default Django UserChangeForm with course limiting functionality.
    """

    class Meta(admin_forms.UserChangeForm.Meta):
        model = User


class UserAdminCreationForm(CourseLimitingFormMixin, admin_forms.UserCreationForm):
    """
    Form for User Creation in the Admin Area.

    This form is used for creating new users through the Django admin interface.
    To change user signup for public registration, see UserSignupForm and
    UserSocialSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):  # type: ignore[name-defined]
        model = User
        # Custom error message for duplicate usernames
        error_messages = {
            "username": {"unique": _("This username has already been taken.")},
        }


class UserSignupForm(SignupForm):
    """
    Form that will be rendered on a user sign up section/screen.

    This form is used for standard email/password registration through
    django-allauth. Default fields will be added automatically by allauth.
    For social account signup, see UserSocialSignupForm.
    """


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.

    This form is used when users register via OAuth providers (Google, Facebook, etc.)
    through django-allauth. Default fields will be added automatically.
    For standard email/password signup, see UserSignupForm.
    """


class AdminUserRegistrationForm(CourseLimitingFormMixin, forms.ModelForm):
    """
    Form for registering a new user through the admin interface.

    This form allows admin users to manually create new user accounts.
    It automatically sets the created_by field and creates a verified
    email address for the new user.
    """

    # Required fields for user registration
    email = forms.EmailField(required=True)
    name = forms.CharField(required=True)
    password = forms.CharField(widget=forms.PasswordInput)
    # Username is optional - will default to email if not provided
    username = forms.CharField(
        required=False,
        help_text="If not provided, email will be used",
    )

    class Meta:
        model = User
        fields = ["email", "username", "password", "name"]

    def clean_email(self):
        """
        Validate that the email address is unique.

        Returns:
            str: The cleaned email address

        Raises:
            forms.ValidationError: If email already exists
        """
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            msg = "A user with this email already exists."
            raise forms.ValidationError(msg)
        return email

    def clean(self):
        """
        Clean and validate form data.

        If username is not provided, automatically use email as username.
        This ensures every user has a username for authentication.

        Returns:
            dict: Cleaned form data
        """
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        email = cleaned_data.get("email")

        # If username is empty, use email as username
        if not username and email:
            cleaned_data["username"] = email

        return cleaned_data

    def save(self, commit=True):  # noqa: FBT002
        """
        Save the user instance with password hashing and email verification.

        Creates a new user with:
        - Hashed password
        - created_by set to the staff user who created this account
        - Verified email address in EmailAddress model

        Args:
            commit: If True, save to database. If False, return unsaved instance.

        Returns:
            User: The created user instance
        """
        # Create user instance without saving
        user = super().save(commit=False)
        # Hash the password before saving
        user.set_password(self.cleaned_data["password"])
        # Set the creator to the staff user performing the action
        user.created_by = self.staff_user

        if commit:
            # Use transaction to ensure atomicity
            with transaction.atomic():
                user.save()
                # Create verified email address for django-allauth
                # This allows the user to login immediately without email verification
                EmailAddress.objects.create(
                    user=user,
                    email=self.cleaned_data["email"],
                    primary=True,
                    verified=True,
                )
        return user


class UserImportForm(forms.Form):
    """
    Form for uploading Excel file containing user data.

    This form validates that the uploaded file is a valid Excel (.xlsx) file
    and contains the required columns (email, password) for bulk user import.
    """

    # File upload field for Excel file
    file = forms.FileField()

    def clean_file(self):
        """
        Validate the uploaded file.

        Checks:
        1. File extension is .xlsx
        2. File can be read as Excel
        3. File contains required columns (email, password)

        Returns:
            UploadedFile: The validated file object

        Raises:
            forms.ValidationError: If file is invalid or missing required columns
        """
        file = self.cleaned_data["file"]
        allowed_extension = ".xlsx"
        # Validate file extension
        if not file.name.endswith(allowed_extension):
            msg = f"Only Excel ({allowed_extension}) files are allowed."
            raise forms.ValidationError(msg)

        # Validate file contents by attempting to read it as Excel
        try:
            # Read Excel file into pandas DataFrame
            df_data = pd.read_excel(io.BytesIO(file.read()))
        except ValueError as e:
            # File is not a valid Excel file
            msg = f"Invalid Excel file: {e!s}"
            raise forms.ValidationError(msg) from e
        else:
            # Check for required columns
            required_columns = ["email", "password"]
            for col in required_columns:
                if col not in df_data.columns:
                    msg = f"Missing required column: {col}"
                    raise forms.ValidationError(msg)

            # Reset file pointer to beginning for later use in view
            # This allows the file to be read again during import processing
            file.seek(0)
            return file
