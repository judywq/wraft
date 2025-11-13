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


class StaffUserFormMixin:
    """
    Mixin to store the staff user who is creating/editing the form.
    """

    def __init__(self, *args, **kwargs):
        # Extract staff_user from kwargs to pass to form initialization
        # This allows forms to know which admin user is performing the action
        admin_user = kwargs.pop("staff_user", None)
        self.staff_user = admin_user
        super().__init__(*args, **kwargs)


class UserAdminCreationForm(StaffUserFormMixin, admin_forms.UserCreationForm):
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


class AdminUserRegistrationForm(StaffUserFormMixin, forms.ModelForm):
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
        email_address = self.cleaned_data["email"]
        if User.objects.filter(email=email_address).exists():
            error_message = "This email address is already registered."
            raise forms.ValidationError(error_message)
        return email_address

    def clean(self):
        """
        Clean and validate form data.

        If username is not provided, automatically use email as username.
        This ensures every user has a username for authentication.

        Returns:
            dict: Cleaned form data
        """
        cleaned_data = super().clean()
        user_email = cleaned_data.get("email")
        user_username = cleaned_data.get("username")

        # If username is empty, use email as username
        if not user_username and user_email:
            cleaned_data["username"] = user_email

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
        new_user = super().save(commit=False)
        user_password = self.cleaned_data["password"]
        user_email = self.cleaned_data["email"]

        # Hash the password before saving
        new_user.set_password(user_password)
        # Set the creator to the staff user performing the action
        new_user.created_by = self.staff_user

        if commit:
            # Use transaction to ensure atomicity
            with transaction.atomic():
                new_user.save()
                # Create verified email address for django-allauth
                # This allows the user to login immediately without email verification
                EmailAddress.objects.create(
                    user=new_user,
                    email=user_email,
                    primary=True,
                    verified=True,
                )
        return new_user


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
        uploaded_file = self.cleaned_data["file"]
        expected_extension = ".xlsx"

        # Validate file extension
        if not uploaded_file.name.endswith(expected_extension):
            error_message = f"File must be an Excel file ({expected_extension})."
            raise forms.ValidationError(error_message)

        # Validate file contents by attempting to read it as Excel
        try:
            file_content = uploaded_file.read()
            # Read Excel file into pandas DataFrame
            dataframe = pd.read_excel(io.BytesIO(file_content))
        except ValueError as exc:
            # File is not a valid Excel file
            error_message = f"Unable to read Excel file: {exc!s}"
            raise forms.ValidationError(error_message) from exc
        else:
            # Check for required columns
            mandatory_columns = ["email", "password"]
            for column_name in mandatory_columns:
                if column_name not in dataframe.columns:
                    error_message = f"Required column '{column_name}' is missing."
                    raise forms.ValidationError(error_message)

            # Reset file pointer to beginning for later use in view
            # This allows the file to be read again during import processing
            uploaded_file.seek(0)
            return uploaded_file
