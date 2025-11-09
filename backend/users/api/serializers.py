"""
REST API serializers for user authentication and management.

This module contains serializers for user registration, login,
and user details in the REST API.
"""
from dj_rest_auth.models import TokenModel
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer
from dj_rest_auth.serializers import UserDetailsSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers

UserModel = get_user_model()


class CustomLoginSerializer(LoginSerializer):
    """
    Custom login serializer that skips email verification for superusers.

    This serializer extends the default login serializer to allow
    superusers to login without email verification, which is useful
    for admin accounts.
    """

    @staticmethod
    def validate_email_verification_status(user, email=None):
        """
        Validate email verification status for login.

        Superusers can login without email verification.
        Regular users must have verified emails.

        Args:
            user: The user attempting to login
            email: Optional email address to check

        Raises:
            ValidationError: If email is not verified (for non-superusers)
        """
        # Skip validation for superusers
        if user.is_superuser:
            return

        # Call parent's static method for regular users
        LoginSerializer.validate_email_verification_status(user, email)


class CustomUserDetailsSerializer(UserDetailsSerializer):
    """
    Serializer for user details without password.

    This serializer dynamically includes user model fields based on
    what fields are available in the UserModel. It excludes the password
    field for security.
    """

    class Meta:
        # Dynamically build extra_fields list based on UserModel
        extra_fields = []
        # Include username field if it exists
        if hasattr(UserModel, "USERNAME_FIELD"):
            extra_fields.append(UserModel.USERNAME_FIELD)
        # Include email field if it exists
        if hasattr(UserModel, "EMAIL_FIELD"):
            extra_fields.append(UserModel.EMAIL_FIELD)
        # Include first_name if it exists (though our model doesn't use it)
        if hasattr(UserModel, "first_name"):
            extra_fields.append("first_name")
        # Include last_name if it exists (though our model doesn't use it)
        if hasattr(UserModel, "last_name"):
            extra_fields.append("last_name")
        model = UserModel
        # Include primary key and all extra fields
        fields = ("pk", *extra_fields)
        # Email is read-only to prevent unauthorized changes
        read_only_fields = ("email",)


class TokenSerializer(serializers.ModelSerializer):
    """
    Serializer for authentication tokens.

    This serializer includes the token key, creation timestamp,
    and user details when returning authentication tokens.
    """

    # Nested serializer for user details
    user = CustomUserDetailsSerializer()

    class Meta:
        model = TokenModel
        # Token key, creation timestamp, and user details
        fields = ["key", "created", "user"]


class CustomRegisterSerializer(RegisterSerializer):
    """
    Custom registration serializer that includes the name field.

    This serializer extends the default registration serializer to
    include the 'name' field, which is required for our User model.
    """

    # Name field is required for user registration
    name = serializers.CharField(required=True)

    def get_cleaned_data(self):
        """
        Get cleaned and validated form data.

        Adds the name field to the cleaned data dictionary.

        Returns:
            dict: Cleaned data including name field
        """
        data = super().get_cleaned_data()
        data["name"] = self.validated_data.get("name", "")
        return data

    def save(self, request):
        """
        Save the new user instance with the name field.

        Creates a new user and sets the name field from the form data.

        Args:
            request: The HTTP request object

        Returns:
            User: The newly created user instance
        """
        # Create user using parent serializer
        user = super().save(request)
        # Set the name field from cleaned data
        user.name = self.cleaned_data.get("name")
        user.save()
        return user
