"""
Django REST Framework serializers for LLM Gateway models.

This module provides serializers for converting model instances to/from
JSON for API responses. Includes custom fields for usage limits and
user-specific data.
"""

from rest_framework import serializers

from .models import LLMRequestRecord
from .models import LLMModel


class LLMModelSerializer(serializers.ModelSerializer):
    """
    Serializer for LLM model instances.

    Includes usage limit information for the current user, showing both
    the daily limit and current usage count.
    """
    # Custom field showing user's current usage count
    used_limit = serializers.SerializerMethodField()
    # Daily limit from the related LimitConfig
    daily_limit = serializers.IntegerField(source="limit_config.daily_limit")

    class Meta:
        model = LLMModel
        fields = [
            "id",
            "order",
            "display_name",
            "used_limit",
            "daily_limit",
        ]

    def get_usage_count(self, model_instance):
        """
        Get the current user's usage count for this model.

        Args:
            model_instance: The LLMModel instance being serialized

        Returns:
            int: The user's usage count for today, or 0 if user not available
        """
        try:
            # Get current user from request context
            current_user = self.context["request"].user
        except (KeyError, AttributeError):
            # Return 0 if user not available in context
            return 0

        # Get usage count for this user and model
        return model_instance.get_usage_count(current_user)


class LLMRequestRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for LLM request record instances.

    Serializes all fields of LLMRequestRecord. Status and created_at
    are read-only as they are managed by the system.
    """
    class Meta:
        model = LLMRequestRecord
        fields = "__all__"
        # Fields that cannot be set via API (managed by system)
        read_only_fields = [
            "status",
            "created_at",
        ]
