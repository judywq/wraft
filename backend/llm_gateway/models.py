"""
Django models for the LLM Gateway application.

This module defines the database models for managing LLM models, configurations,
API keys, request records, and settings. It includes abstract base models for
common functionality like timestamps and task tracking.
"""

import os

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.core.validators import URLValidator
from django.db import models

from .settings import LLM_PURPOSE_CHOICES
from .helpers import get_today_date_range

from backend.common.models import TimeStampedModel
from backend.common.models import TaskModelBase
from backend.common.models import STATUSES_FOR_LIMIT_CHECK

UserModel = get_user_model()


class UserCreatableModel(models.Model):
    """
    Abstract base model that tracks the user who created the record.

    Provides a foreign key to the User model to track ownership and
    enable user-specific filtering and permissions.
    """

    # User who created this record (set to NULL if user is deleted)
    created_by = models.ForeignKey(
        UserModel,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="%(class)s_created",
    )

    class Meta:
        abstract = True


class LLMModel(TimeStampedModel):
    """
    Represents an LLM (Large Language Model) available in the system.

    Stores information about LLM models including their API names, display names,
    and configuration. Models can be activated/deactivated and ordered for
    display in the UI. Each model can have associated API keys and usage limits.
    """
    # Display order in UI (lower numbers appear first)
    order = models.IntegerField(
        default=10,
        help_text="Order of the model in the UI (smaller number comes first)",
    )
    # API identifier for the model (e.g., "openai/gpt-4o-mini")
    name = models.CharField(
        max_length=200,
        help_text=(
            "The model name for calling the LLM API (e.g., openai/gpt-4o-mini)."
            " Check <a href='https://docs.litellm.ai/docs/providers'"
            " target='_blank'>Litellm model list</a>."
        ),
    )
    # Human-readable name displayed in the UI (e.g., "GPT-4o")
    display_name = models.CharField(
        max_length=200,
        help_text="Display name for the model (e.g., GPT-4o)",
    )
    # Whether this model is currently available for use
    is_active = models.BooleanField(
        default=True,
        help_text="Only active models will be listed in the UI",
    )

    class Meta:
        ordering = ["order"]
        get_latest_by = "created_at"
        verbose_name = "Model"
        verbose_name_plural = "Models"

    def __str__(self):
        """String representation showing display name and active status."""
        active_status = "Active" if self.is_active else "Inactive"
        return f"{self.display_name} ({active_status})"

    @classmethod
    def get_active_models(cls):
        """
        Retrieve all active models.

        Returns:
            QuerySet: QuerySet of active LLMModel instances
        """
        return cls.objects.filter(is_active=True)

    def get_usage_count(self, user) -> int:
        """
        Calculate the number of requests made by this user today for this model.

        Counts all requests with valid statuses (PENDING, PROCESSING, COMPLETED)
        within today's date range. Failed requests are not counted.

        Args:
            user: The User instance to count usage for

        Returns:
            int: Number of requests made today
        """
        # Get today's date range (start and end of current day)
        start_time, end_time = get_today_date_range()

        # Count requests with valid statuses within today's range
        return LLMRequestRecord.objects.filter(
            created_by=user,
            model=self,
            status__in=STATUSES_FOR_LIMIT_CHECK,
            created_at__range=(start_time, end_time),
        ).count()

    def is_limit_exceeded(self, user) -> bool:
        """
        Check if the user has exceeded the daily limit for this model.

        If no limit configuration exists for this model, returns False
        (unlimited usage). Otherwise, compares current usage against
        the configured daily limit.

        Args:
            user: The User instance to check limits for

        Returns:
            bool: True if limit is exceeded, False otherwise
        """
        try:
            # Get the limit configuration for this model
            limit = self.limit_config
        except LimitConfig.DoesNotExist:
            # Missing limit config implies unlimited usage
            return False
        # Get current usage count for today
        current_usage = self.get_usage_count(user)
        # Check if usage meets or exceeds the limit
        return current_usage >= limit.daily_limit


class LimitConfig(TimeStampedModel):
    """
    Configuration for daily usage limits per LLM model.

    Each LimitConfig defines the maximum number of requests allowed per day
    for a specific model. If no LimitConfig exists for a model, usage is unlimited.
    Uses a OneToOne relationship - each model can have at most one limit config.
    """
    # One-to-one relationship: each model has one limit config
    model = models.OneToOneField(
        LLMModel,
        on_delete=models.CASCADE,
        related_name="limit_config",
        help_text="The LLM model this limit applies to",
    )
    # Maximum number of requests allowed per day
    daily_limit = models.IntegerField(
        default=10,
        help_text="Maximum number of requests per day for this model",
    )

    class Meta:
        get_latest_by = "created_at"
        verbose_name = "Model Limit"
        verbose_name_plural = "Model Limits"

    def __str__(self):
        """String representation showing model name and limit value."""
        return f"LimitConfig({self.model.display_name}, limit={self.daily_limit})"


class LLMRequestRecord(TaskModelBase, UserCreatableModel):
    """
    Records for LLM API endpoint requests.

    Tracks all LLM API requests made through the gateway, including input data,
    prompts, responses, and execution status. Inherits task tracking from
    TaskModelBase and user tracking from UserCreatableModel.
    """

    # Additional metadata associated with the request (optional)
    meta_data = models.JSONField(
        blank=True,
        default=dict,
        help_text="Meta data for the request",
    )
    # Input data in JSON format used to fill the prompt template
    input_json = models.JSONField(
        blank=True,
        default=dict,
        help_text="Input JSON to be filled in the prompt",
    )
    # Raw text response from the LLM API
    result = models.TextField(
        blank=True,
        default="",
        help_text="The raw response from the LLM",
    )
    # The prompt template used (before formatting with input_json)
    user_prompt_template = models.TextField(
        blank=True,
        default="",
        help_text="The user prompt template",
    )
    # The actual formatted prompt sent to the LLM
    user_prompt = models.TextField(
        blank=True,
        default="",
        help_text="The actual prompt sent to the LLM",
    )
    # The LLM model used for this request (protected from deletion)
    model = models.ForeignKey(
        LLMModel,
        on_delete=models.PROTECT,
        related_name="requests",
        help_text="The LLM model used for this request",
    )
    # Temperature setting for the LLM (controls randomness)
    temperature = models.FloatField(
        default=0.7,
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(2.0),
        ],
    )
    # Soft delete flag - marks record as deleted without removing from database
    is_deleted = models.BooleanField(
        default=False,
        help_text="Soft delete flag - True means this request is deleted",
    )

    class Meta:
        ordering = ["-created_at"]  # Most recent first
        verbose_name = "LLM Request Record"
        verbose_name_plural = "LLM Request Records"

    def __str__(self):
        """String representation showing creator, status, and model."""
        return f"LLMRequestRecord(created_by={self.created_by}, status={self.status}, \
            model={self.model.display_name})"


class ModelConfig(TimeStampedModel):
    """
    Configuration for LLM models for specific purposes.

    Links LLM models to specific use cases (purposes) with custom prompt templates,
    temperature settings, and example outputs. Only one config can be active
    per purpose at a time. Used for testing with fake mode and example outputs.
    """
    # The purpose/use case for this configuration (e.g., "score", "correction")
    purpose = models.CharField(
        max_length=50,
        choices=LLM_PURPOSE_CHOICES,
        help_text="The purpose of this configuration",
    )
    # The LLM model to use for this purpose (set to NULL if model is deleted)
    model = models.ForeignKey(
        LLMModel,
        on_delete=models.SET_NULL,
        related_name="llm_configs",
        help_text="The LLM model this config applies to",
        null=True,
    )
    # Prompt template with placeholders for formatting with input data
    user_prompt_template = models.TextField(
        help_text="The user prompt template for the LLM.",
    )
    # Temperature setting for the LLM (0.0-2.0, controls randomness)
    temperature = models.FloatField(
        default=0.7,
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(2.0),
        ],
        help_text="Value between 0 and 2",
    )
    # Example output used in fake mode for testing/debugging
    example_output = models.TextField(
        blank=True,
        default="",
        help_text="Example output. Will be used as the fake response for debugging.",
    )
    # Delay in seconds when running in fake mode (for testing)
    delay_seconds_in_fake_mode = models.IntegerField(
        default=0,
        help_text="The delay in seconds for LLM requests in fake mode",
    )
    # Whether this config is currently active (only one per purpose)
    is_active = models.BooleanField(
        default=False,
        help_text="Only one config can be active per purpose",
    )

    class Meta:
        get_latest_by = "created_at"
        verbose_name = "Model Config"
        verbose_name_plural = "Model Configs"

    def __str__(self):
        """String representation showing purpose and update time."""
        purpose_display = self.get_purpose_display()
        return f"LLM Config ({purpose_display}, Updated: {self.updated_at})"

    def save(self, *args, **kwargs):
        """
        Override save to enforce single active config per purpose.

        When a config is marked as active, all other configs with the same
        purpose are automatically deactivated to maintain uniqueness.
        """
        if self.is_active:
            # Disable other configs sharing the same purpose
            # This ensures only one active config exists per purpose
            ModelConfig.objects.filter(purpose=self.purpose).exclude(id=self.id).update(
                is_active=False,
            )
        super().save(*args, **kwargs)

    @classmethod
    def get_active_config(
        cls,
        purpose: str,
    ):
        """
        Retrieve the active configuration for a specific purpose.

        Gets the currently active ModelConfig for the given purpose.
        Raises ValueError if no active config exists, which should be
        handled by creating a config in the admin panel.

        Args:
            purpose: The purpose string to get config for

        Returns:
            ModelConfig: The active config for the purpose

        Raises:
            ValueError: If no active config exists for the purpose
        """
        try:
            return cls.objects.get(purpose=purpose, is_active=True)
        except cls.DoesNotExist:
            error_message = (
                f"No active config found for purpose: {purpose}."
                f"Please create one in the admin panel."
            )
            raise ValueError(error_message) from None


class APIKey(TimeStampedModel):
    """
    Stores API keys for LLM providers.

    Manages API keys for different LLM providers. Keys can be associated
    with specific models or used globally via environment variable names.
    Keys can be activated/deactivated without deletion.
    """
    # Optional association with a specific model (null for global keys)
    model = models.ForeignKey(
        LLMModel,
        on_delete=models.CASCADE,
        related_name="api_keys",
        help_text="The LLM model this key is associated with",
        null=True,
        blank=True,
    )
    # Environment variable name for global keys (e.g., "OPENAI_API_KEY")
    name = models.CharField(
        max_length=255,
        help_text="Name of the environment variable (e.g, OPENAI_API_KEY)",
        default="",
        blank=True,
    )
    # The actual API key value (stored securely)
    key = models.CharField(
        max_length=255,
        help_text="The API key (e.g., OpenAI starts with 'sk-')",
    )
    # Whether this key is currently active and should be used
    is_active = models.BooleanField(
        default=True,
        help_text="Only active keys will be used",
    )

    class Meta:
        ordering = ["created_at"]  # Oldest first
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"

    def __str__(self):
        """String representation showing key name and active status."""
        key_name = self.model.display_name if self.model else self.name
        status_text = "Active" if self.is_active else "Inactive"
        return f"{key_name} API Key ({status_text})"

    def clean(self):
        """
        Validate that either model or name is provided.

        Ensures that each API key is either associated with a model
        or has an environment variable name for global use.

        Raises:
            ValidationError: If neither model nor name is provided
        """
        super().clean()
        if not self.model and not self.name:
            raise ValidationError(
                {"model": "Either model or name must be provided"},
            )

    @classmethod
    def apply_all_keys_to_env(cls):
        """
        Apply all active API keys to the environment.

        Sets environment variables for all active keys that have a name.
        This allows the LLM library to access keys via environment variables.
        """
        # Get all active keys
        active_keys = cls.objects.filter(is_active=True)
        # Set environment variables for keys with names
        for api_key in active_keys:
            if api_key.name:
                os.environ[api_key.name] = api_key.key

    @classmethod
    def get_available_key(
        cls,
        model_id: int,
        default_key: str | None = None,
    ) -> str | None:
        """
        Retrieve the first available active key for the specified model.

        Gets the oldest active API key associated with the given model.
        Returns the default key if no active key is found for the model.

        Args:
            model_id: The ID of the LLM model to get a key for
            default_key: Optional default key to return if none found

        Returns:
            str | None: The API key string, or default_key if none found
        """
        # Get the oldest active key for this model
        key_obj = (
            cls.objects.filter(
                model__id=model_id,
                is_active=True,
            )
            .order_by("created_at")  # Get oldest first
            .first()
        )
        # Return default if no key found
        if key_obj is None:
            return default_key
        return key_obj.key


class LLMSettings(TimeStampedModel):
    """
    Global settings for LLM functionality.

    Implements a singleton pattern - only one instance can exist.
    Controls global behavior like fake mode (for testing) and task delays.
    """
    # If True, LLM requests return fake responses instead of making real API calls
    fake_llm_request = models.BooleanField(
        default=False,
        help_text=(
            "If True, LLM requests will return fake responses instead of "
            "making real API calls"
        ),
    )
    # Delay in seconds before processing LLM requests (for testing/throttling)
    task_delay_seconds = models.IntegerField(
        default=0,
        help_text="The delay in seconds for LLM requests",
    )

    class Meta:
        verbose_name = "LLM Settings"
        verbose_name_plural = "LLM Settings"

    def __str__(self):
        """String representation showing it's the global settings."""
        return "LLM Settings"

    def save(self, *args, **kwargs):
        """
        Override save to enforce singleton pattern.

        Prevents creation of multiple settings instances. Only one
        LLMSettings instance can exist at a time.

        Raises:
            ValidationError: If attempting to create a second instance
        """
        # Enforce singleton pattern - only one instance allowed
        if self.pk is None and LLMSettings.objects.exists():
            raise ValidationError("Only one LLM Settings instance can exist")
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """
        Retrieve current LLM settings, creating if necessary.

        Gets the singleton settings instance. If none exists, creates one
        with default values. This ensures settings always exist.

        Returns:
            LLMSettings: The singleton settings instance
        """
        settings_obj, created = cls.objects.get_or_create()
        return settings_obj
