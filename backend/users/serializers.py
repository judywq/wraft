"""
Serializers powering auth and user endpoints.

These serializers wrap dj-rest-auth behavior with a few tweaks:
- Superusers can bypass email verification on login
- User detail output is dynamically shaped from the active user model
- Registration accepts an extra required `name` field
- Token responses include nested user info
"""

from django.contrib.auth import get_user_model
from dj_rest_auth.models import TokenModel
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer, UserDetailsSerializer
from rest_framework import serializers

UserModel = get_user_model()


# ---------- Login ----------

class CustomLoginSerializer(LoginSerializer):
    """
    Same as dj-rest-auth's LoginSerializer, except superusers are allowed
    to sign in without verified email.
    """

    @staticmethod
    def validate_email_verification_status(user, email=None):
        # Let admins in even if email isn't verified
        if getattr(user, "is_superuser", False):
            return
        # Defer to the base class for everyone else
        return LoginSerializer.validate_email_verification_status(user, email)


# ---------- User details ----------

def _computed_user_fields():
    """
    Create the field list for the user details serializer at import time.

    We always include pk and (if present) the model's declared username/email
    fields, plus optional first_name/last_name for compatibility.
    """
    fields = ["pk"]
    uname = getattr(UserModel, "USERNAME_FIELD", None)
    if uname:
        fields.append(uname)
    email_field_name = getattr(UserModel, "EMAIL_FIELD", None)
    if email_field_name:
        fields.append(email_field_name)
    if hasattr(UserModel, "first_name"):
        fields.append("first_name")
    if hasattr(UserModel, "last_name"):
        fields.append("last_name")
    # Keep order while avoiding duplicates
    seen, ordered = set(), []
    for f in fields:
        if f not in seen:
            seen.add(f)
            ordered.append(f)
    return tuple(ordered)


class CustomUserDetailsSerializer(UserDetailsSerializer):
    """
    Exposes a slim, password-free view of the user model. The concrete
    list of fields is computed dynamically from the active user model.
    """

    class Meta:
        model = UserModel
        fields = _computed_user_fields()
        read_only_fields = ("email",)  # guard against unsafe email changes


# ---------- Token with embedded user ----------

class TokenSerializer(serializers.ModelSerializer):
    """
    Token payload that also returns basic user information.
    """
    user = CustomUserDetailsSerializer(read_only=True)

    class Meta:
        model = TokenModel
        fields = ["key", "created", "user"]


# ---------- Registration with extra `name` ----------

class CustomRegisterSerializer(RegisterSerializer):
    """
    Extends registration to capture a required `name` attribute and
    persists it to the created user instance.
    """
    name = serializers.CharField(required=True)

    def get_cleaned_data(self):
        base = super().get_cleaned_data()
        base["name"] = self.validated_data.get("name", "")
        return base

    def save(self, request):
        user = super().save(request)
        # Persist the custom field onto the user record
        user.name = self.cleaned_data.get("name")
        user.save(update_fields=["name"])
        return user
