import logging
import os

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.core.validators import URLValidator
from django.db import models

from .settings import LLM_PURPOSE_CHOICES
from .utils import get_today_date_range

logger = logging.getLogger(__name__)

User = get_user_model()


class TimestampedBase(models.Model):
    """Base model that adds created_at and updated_at timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TaskBase(TimestampedBase):
    """Base model that adds task-related timestamps."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        ABORTED = "ABORTED", "Aborted"

    task_id = models.CharField(max_length=255, default="", blank=True)
    status = models.CharField(
        max_length=255,
        choices=Status.choices,
        default=Status.PENDING,
        blank=True,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(
        blank=True,
        default="",
        help_text="Error message that displays to the user.",
    )
    error_details = models.TextField(
        blank=True,
        default="",
        help_text="Error details to diagnose the error.",
    )

    class Meta:
        abstract = True


class CreatableBase(models.Model):
    """
    Abstract base model that adds a created_by field.
    """

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="%(class)s_created",
    )

    class Meta:
        abstract = True


QUOTA_USAGE_STATUS = [
    TaskBase.Status.PENDING,
    TaskBase.Status.PROCESSING,
    TaskBase.Status.COMPLETED,
]


class LLMModel(TimestampedBase):
    order = models.IntegerField(
        default=10,
        help_text="Order of the model in the UI (smaller number comes first)",
    )
    name = models.CharField(
        max_length=200,
        help_text=(
            "The model name for calling the LLM API (e.g., openai/gpt-4o-mini)."
            " Check <a href='https://docs.litellm.ai/docs/providers'"
            " target='_blank'>Litellm model list</a>."
        ),
    )
    display_name = models.CharField(
        max_length=200,
        help_text="Display name for the model (e.g., GPT-4o)",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="This model will be pre-selected in the UI",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only active models will be listed in the UI",
    )
    url = models.URLField(
        max_length=500,
        blank=True,
        help_text=(
            "URL for third-party LLM service "
            "(e.g., http://host.docker.internal:8080/v1). "
            "Leave empty for hosted models."
        ),
        validators=[URLValidator()],
    )

    class Meta:
        ordering = ["order"]
        get_latest_by = "created_at"
        verbose_name = "Model"
        verbose_name_plural = "Models"

    def __str__(self):
        return f"{self.display_name} ({'Active' if self.is_active else 'Inactive'})"

    def save(self, *args, **kwargs):
        # If this model is being set as default, reset all others
        if self.is_default:
            LLMModel.objects.exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_active_models(cls):
        return cls.objects.filter(is_active=True)

    def get_used_quota(self, user) -> int:
        """Get the number of completed requests for today for this model and user."""
        today_start, today_end = get_today_date_range()

        # Calculate the number of completed requests for today
        # status is either PENDING or COMPLETED
        return APIRequest.objects.filter(
            created_by=user,
            model=self,
            status__in=QUOTA_USAGE_STATUS,
            created_at__range=(today_start, today_end),
        ).count()

    def check_quota(self, user) -> bool:
        """
        Check if the user still has enough quota for this model.
        Returns True if the user has remaining quota
                False if the user has exceeded their quota.
        """
        try:
            quota_config = self.quota_config
        except QuotaConfig.DoesNotExist:
            # No quota config means unlimited requests
            return True

        used_quota = self.get_used_quota(user)
        return used_quota < quota_config.daily_limit

    def clean(self):
        super().clean()
        if self.name:
            first_part = self.name.split("/")[0]
            if first_part in ["custom", "ollama"] and not self.url:
                raise ValidationError(
                    {"url": "URL is required for custom and third-party LLM services"},
                )


class QuotaConfig(TimestampedBase):
    model = models.OneToOneField(
        LLMModel,
        on_delete=models.CASCADE,
        related_name="quota_config",
        help_text="The LLM model this quota applies to",
    )
    daily_limit = models.IntegerField(
        default=10,
        help_text="Maximum number of requests per day for this model",
    )

    class Meta:
        get_latest_by = "created_at"
        verbose_name = "Model Quota"
        verbose_name_plural = "Model Quotas"

    def __str__(self):
        return f"QuotaConfig({self.model.display_name}, limit={self.daily_limit})"


class APIRequest(TaskBase, CreatableBase):
    """Individual API requests."""

    meta_data = models.JSONField(
        blank=True,
        default=dict,
        help_text="Meta data for the request",
    )
    input_json = models.JSONField(
        blank=True,
        default=dict,
        help_text="Input JSON to be filled in the prompt",
    )
    result = models.TextField(
        blank=True,
        default="",
        help_text="The raw response from the LLM",
    )
    user_prompt_template = models.TextField(
        blank=True,
        default="",
        help_text="The user prompt template",
    )
    user_prompt = models.TextField(
        blank=True,
        default="",
        help_text="The actual prompt sent to the LLM",
    )
    model = models.ForeignKey(
        LLMModel,
        on_delete=models.PROTECT,
        related_name="requests",
        help_text="The LLM model used for this request",
    )
    temperature = models.FloatField(
        default=0.7,
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(2.0),
        ],
    )
    is_deleted = models.BooleanField(
        default=False,
        help_text="Soft delete flag - True means this request is deleted",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Request"
        verbose_name_plural = "Requests"

    def __str__(self):
        return f"APIRequest(created_by={self.created_by}, status={self.status}, \
            model={self.model.display_name})"


class LLMConfig(TimestampedBase):
    purpose = models.CharField(
        max_length=50,
        choices=LLM_PURPOSE_CHOICES,
        help_text="The purpose of this configuration",
    )
    model = models.ForeignKey(
        LLMModel,
        on_delete=models.SET_NULL,
        related_name="llm_configs",
        help_text="The LLM model this config applies to",
        null=True,
    )
    user_prompt_template = models.TextField(
        help_text="The user prompt template for the LLM.",
    )
    temperature = models.FloatField(
        default=0.7,
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(2.0),
        ],
        help_text="Value between 0 and 2",
    )
    example_output = models.TextField(
        blank=True,
        default="",
        help_text="Example output. Will be used as the fake response for debugging.",
    )
    delay_seconds_in_fake_mode = models.IntegerField(
        default=0,
        help_text="The delay in seconds for LLM requests in fake mode",
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Only one config can be active per purpose",
    )

    class Meta:
        get_latest_by = "created_at"
        verbose_name = "Model Config"
        verbose_name_plural = "Model Configs"

    def __str__(self):
        return f"LLM Config ({self.get_purpose_display()}, Updated: {self.updated_at})"

    def save(self, *args, **kwargs):
        if self.is_active:
            # Deactivate other configs with the same purpose
            LLMConfig.objects.filter(purpose=self.purpose).exclude(id=self.id).update(
                is_active=False,
            )
        super().save(*args, **kwargs)

    @classmethod
    def get_active_config(
        cls,
        purpose: str,
    ):
        """Get the active config for the given purpose."""
        try:
            return cls.objects.get(purpose=purpose, is_active=True)
        except cls.DoesNotExist:
            msg = (
                f"No active config found for purpose: {purpose}."
                f"Please create one in the admin panel."
            )
            raise ValueError(msg) from None


class APIKey(TimestampedBase):
    model = models.ForeignKey(
        LLMModel,
        on_delete=models.CASCADE,
        related_name="api_keys",
        help_text="The LLM model this key is associated with",
        null=True,
        blank=True,
    )
    name = models.CharField(
        max_length=255,
        help_text="Name of the environment variable (e.g, OPENAI_API_KEY)",
        default="",
        blank=True,
    )
    key = models.CharField(
        max_length=255,
        help_text="Value of the API key (e.g., OpenAI starts with 'sk-')",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only active keys will be used",
    )

    class Meta:
        ordering = ["created_at"]
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"

    def __str__(self):
        name = self.model.display_name if self.model else self.name
        return f"{name} API Key ({'Active' if self.is_active else 'Inactive'})"

    def clean(self):
        super().clean()
        if not self.model and not self.name:
            raise ValidationError(
                {"model": "Either model or name must be provided"},
            )

    @classmethod
    def apply_all_keys_to_env(cls):
        for key in cls.objects.filter(is_active=True):
            if key.name:
                os.environ[key.name] = key.key

    @classmethod
    def get_available_key(
        cls,
        model_id: int,
        default_key: str | None = None,
    ) -> str | None:
        """Get the first available active key for the specified model."""
        obj = (
            cls.objects.filter(
                model__id=model_id,
                is_active=True,
            )
            .order_by("created_at")
            .first()
        )
        if not obj:
            return default_key
        return obj.key


class LLMSettings(TimestampedBase):
    """Global settings for LLM functionality."""

    fake_llm_request = models.BooleanField(
        default=False,
        help_text=(
            "If True, LLM requests will return fake responses instead of "
            "making real API calls"
        ),
    )
    task_delay_seconds = models.IntegerField(
        default=0,
        help_text="The delay in seconds for LLM requests",
    )

    class Meta:
        verbose_name = "LLM Settings"
        verbose_name_plural = "LLM Settings"

    def __str__(self):
        return "LLM Settings"

    def save(self, *args, **kwargs):
        # Ensure only one settings instance exists
        if not self.pk and LLMSettings.objects.exists():
            error_msg = "Only one LLM Settings instance can exist"
            raise ValidationError(error_msg)
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get the current LLM settings, creating them if they don't exist."""
        settings, _ = cls.objects.get_or_create()
        return settings
