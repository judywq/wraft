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
from .helpers import today_bounds_local

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

    order = models.IntegerField(
        default=10,
        help_text="Controls the display order in the interface (lower numbers appear earlier).",
    )
    name = models.CharField(
        max_length=200,
        help_text=(
            "API identifier used when calling the LLM (e.g., openai/gpt-4o-mini). "
            "Refer to the <a href='https://docs.litellm.ai/docs/providers' target='_blank'>Litellm model catalog</a> for valid names."
        ),
    )
    display_name = models.CharField(
        max_length=200,
        help_text="Readable name shown in the interface (e.g., GPT-4o).",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="If disabled, this model will not be available in the interface.",
    )

    class Meta:
        ordering = ["order"]
        get_latest_by = "created_at"
        verbose_name = "Model"
        verbose_name_plural = "Models"

    def __str__(self):
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
        start_time, end_time = today_bounds_local()

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

    model = models.OneToOneField(
        LLMModel,
        on_delete=models.CASCADE,
        related_name="limit_config",
        help_text="Specifies which LLM model this limit applies to.",
    )
    daily_limit = models.IntegerField(
        default=10,
        help_text="Maximum number of requests allowed per user per day for this model.",
    )

    class Meta:
        get_latest_by = "created_at"
        verbose_name = "Model Limit"
        verbose_name_plural = "Model Limits"

    def __str__(self):
        return f"LimitConfig({self.model.display_name}, limit={self.daily_limit})"


class LLMRequestRecord(TaskModelBase, UserCreatableModel):
    """
    Records for LLM API endpoint requests.

    Tracks all LLM API requests made through the gateway, including input data,
    prompts, responses, and execution status. Inherits task tracking from
    TaskModelBase and user tracking from UserCreatableModel.
    """

    meta_data = models.JSONField(
        blank=True,
        default=dict,
        help_text="Optional metadata providing extra context for this request.",
    )
    input_json = models.JSONField(
        blank=True,
        default=dict,
        help_text="JSON input data used to populate placeholders in the prompt.",
    )
    result = models.TextField(
        blank=True,
        default="",
        help_text="Raw response text returned from the LLM API.",
    )
    user_prompt_template = models.TextField(
        blank=True,
        default="",
        help_text="The original prompt template prior to variable substitution.",
    )
    user_prompt = models.TextField(
        blank=True,
        default="",
        help_text="The actual prompt string sent to the LLM API.",
    )
    model = models.ForeignKey(
        LLMModel,
        on_delete=models.PROTECT,
        related_name="requests",
        help_text="Which LLM model was used to handle this request.",
    )
    temperature = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.0), MaxValueValidator(2.0)],
    )
    is_deleted = models.BooleanField(
        default=False,
        help_text="Marks this record as deleted without removing it from the database.",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "LLM Request Record"
        verbose_name_plural = "LLM Request Records"

    def __str__(self):
        return f"LLMRequestRecord(created_by={self.created_by}, status={self.status}, model={self.model.display_name})"


class ModelConfig(TimeStampedModel):
    """
    Configuration for LLM models for specific purposes.

    Links LLM models to specific use cases (purposes) with custom prompt templates,
    temperature settings, and example outputs. Only one config can be active
    per purpose at a time. Used for testing with fake mode and example outputs.
    """

    purpose = models.CharField(
        max_length=50,
        choices=LLM_PURPOSE_CHOICES,
        help_text="Select the intended function or use case for this configuration.",
    )
    model = models.ForeignKey(
        LLMModel,
        on_delete=models.SET_NULL,
        related_name="llm_configs",
        help_text="The model linked to this configuration (can be left blank if removed).",
        null=True,
    )
    user_prompt_template = models.TextField(
        help_text="Prompt pattern including placeholders for variable data.",
    )
    temperature = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.0), MaxValueValidator(2.0)],
        help_text="Randomness control: a value between 0.0 and 2.0.",
    )
    example_output = models.TextField(
        blank=True,
        default="",
        help_text="Sample output used when running in fake mode for debugging.",
    )
    delay_seconds_in_fake_mode = models.IntegerField(
        default=0,
        help_text="Artificial delay (in seconds) to simulate processing time in fake mode.",
    )
    is_active = models.BooleanField(
        default=False,
        help_text="If enabled, this will be the active configuration for the selected purpose.",
    )

    class Meta:
        get_latest_by = "created_at"
        verbose_name = "Model Config"
        verbose_name_plural = "Model Configs"

    def __str__(self):
        purpose_display = self.get_purpose_display()
        return f"LLM Config ({purpose_display}, Updated: {self.updated_at})"

    def save(self, *args, **kwargs):
        """
        Override save to enforce single active config per purpose.

        When a config is marked as active, all other configs with the same
        purpose are automatically deactivated to maintain uniqueness.
        """
        if self.is_active:
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
            raise ValueError(
                f"No active configuration found for '{purpose}'. Please create or enable one in the admin interface."
            ) from None


class APIKey(TimeStampedModel):
    """
    Stores API keys for LLM providers.

    Manages API keys for different LLM providers. Keys can be associated
    with specific models or used globally via environment variable names.
    Keys can be activated/deactivated without deletion.
    """

    model = models.ForeignKey(
        LLMModel,
        on_delete=models.CASCADE,
        related_name="api_keys",
        help_text="Model linked to this API key (leave blank if it’s a global key).",
        null=True,
        blank=True,
    )
    name = models.CharField(
        max_length=255,
        help_text="Environment variable name (e.g., OPENAI_API_KEY).",
        default="",
        blank=True,
    )
    key = models.CharField(
        max_length=255,
        help_text="Actual API key string (e.g., OpenAI keys usually start with 'sk-').",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive keys will be ignored when making requests.",
    )

    class Meta:
        ordering = ["created_at"]
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"

    def __str__(self):
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
                {"model": "Each API key must be tied to a model or have an environment variable name."},
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
        key_obj = (
            cls.objects.filter(model__id=model_id, is_active=True)
            .order_by("created_at")
            .first()
        )
        return key_obj.key if key_obj else default_key


class LLMSettings(TimeStampedModel):
    """
    Global settings for LLM functionality.

    Implements a singleton pattern - only one instance can exist.
    Controls global behavior like fake mode (for testing) and task delays.
    """

    fake_llm_request = models.BooleanField(
        default=False,
        help_text="When enabled, fake responses are returned instead of real API calls (useful for testing).",
    )
    task_delay_seconds = models.IntegerField(
        default=0,
        help_text="Adds a delay (in seconds) before executing LLM tasks, useful for throttling or testing.",
    )

    class Meta:
        verbose_name = "LLM Settings"
        verbose_name_plural = "LLM Settings"

    def __str__(self):
        return "LLM Settings"

    def save(self, *args, **kwargs):
        """
        Override save to enforce singleton pattern.

        Prevents creation of multiple settings instances. Only one
        LLMSettings instance can exist at a time.

        Raises:
            ValidationError: If attempting to create a second instance
        """
        if self.pk is None and LLMSettings.objects.exists():
            raise ValidationError("Only one instance of LLMSettings is allowed.")
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
