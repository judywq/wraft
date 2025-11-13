"""
Django models for the essay evaluation application.

This module defines models for essay evaluations, including the essay text,
corrections, scores, and usage limits. Models inherit from core base models
for common functionality like timestamps and task tracking.
"""

from django.core.exceptions import ValidationError
from django.db import models

from backend.common.models import CreatableBase
from backend.common.models import TaskModelBase
from backend.common.models import STATUSES_FOR_LIMIT_CHECK
from backend.llm_gateway.helpers import today_bounds_local


class EvaluationLimitManager(models.Manager):
    """
    Custom manager for EvaluationLimit model.

    Provides methods for retrieving active limit configurations.
    """
    def get_active(self):
        """
        Retrieve the currently active limit configuration.

        Returns the active EvaluationLimit instance, or None if no active
        limit exists or multiple active limits exist (invalid state).

        Returns:
            EvaluationLimit | None: The active limit, or None if not found
        """
        try:
            return self.get(is_active=True)
        except (EvaluationLimit.DoesNotExist, EvaluationLimit.MultipleObjectsReturned):
            return None


class EvaluationLimit(models.Model):
    """
    Configuration for daily usage limits for essay evaluations.

    Defines the maximum number of essay evaluations allowed per day per user.
    Only one limit can be active at a time. If no active limit exists,
    usage is unlimited.
    """
    # Maximum number of evaluations allowed per day per user
    daily_limit = models.IntegerField(
        default=10,
        help_text="Maximum number of requests per day.",
    )
    # Whether this limit configuration is currently active
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the limit is active.",
    )
    objects = EvaluationLimitManager()

    class Meta:
        get_latest_by = "created_at"
        verbose_name = "Limit"
        verbose_name_plural = "Limits"

    def __str__(self):
        """String representation showing the limit value."""
        return f"EvaluationLimit(limit={self.daily_limit})"

    def save(self, *args, **kwargs):
        """
        Override save to enforce single active limit.

        When a limit is marked as active, all other active limits are
        automatically deactivated to maintain uniqueness.

        Raises:
            ValidationError: If attempting to activate when another limit is active
        """
        if self.is_active:
            # Verify no other active limit exists
            active_limits = EvaluationLimit.objects.filter(is_active=True)
            # Exclude this instance if updating (not creating)
            if self.pk:
                active_limits = active_limits.exclude(pk=self.pk)

            # Prevent multiple active limits
            if active_limits.exists():
                error_message = "There can only be one active limit at a time."
                raise ValidationError(error_message)
        super().save(*args, **kwargs)


class EssayEvaluation(TaskModelBase, CreatableBase):
    """
    Model for essay evaluation records.

    Stores essay text, prompts, corrections (surface and deep), scores,
    and processing status. Inherits task tracking from TaskModelBase
    and user tracking from CreatableBase. Automatically cleans carriage
    returns from text fields on save.
    """
    # The prompt/question for the essay
    essay_prompt = models.TextField(
        max_length=1000,
        default="",
        blank=True,
        help_text="The prompt for the essay.",
    )
    # The original essay text submitted by the user
    essay_text = models.TextField(
        max_length=5000,
        blank=False,
        help_text="The essay text.",
    )
    # The corrected version of the essay text (after surface correction)
    essay_text_corrected = models.TextField(
        max_length=5000,
        default="",
        blank=True,
        help_text="The corrected essay text.",
    )
    # Surface-level corrections (grammar, spelling, etc.) in JSON format
    surface_correction = models.JSONField(
        default=dict,
        blank=True,
        help_text="The surface level correction of the essay.",
    )
    # Deep-level corrections (structure, content, etc.) in JSON format
    deep_correction = models.JSONField(
        default=dict,
        blank=True,
        help_text="The deep level correction of the essay.",
    )
    # The score assigned to the essay (0.0-100.0 or similar)
    score = models.FloatField(
        null=True,
        blank=True,
        help_text="The score of the essay.",
    )
    # Counter for tracking completed processing tasks (out of 4 total)
    completed_tasks = models.IntegerField(
        default=0,
        help_text="Number of completed processing tasks.",
    )

    class Meta:
        ordering = ["-created_at"]  # Most recent first
        verbose_name = "Usage"
        verbose_name_plural = "Usages"

    def __str__(self):
        """String representation showing first 10 characters of essay text."""
        return f"Essay Evaluation for {self.essay_text[:10]}..."

    def save(self, *args, **kwargs):
        """
        Override save to clean carriage returns from text fields.

        Removes carriage return characters (\r) from text fields to ensure
        consistent line endings. Only processes fields that have changed
        to avoid unnecessary processing.
        """
        # Fields that may contain carriage returns
        text_fields = ["essay_prompt", "essay_text", "essay_text_corrected"]

        def remove_carriage_returns(field_name):
            """Remove carriage returns from a field."""
            field_value = getattr(self, field_name)
            if "\r" in field_value:
                setattr(self, field_name, field_value.replace("\r", ""))

        if self.pk:
            # Existing instance - only clean changed fields
            # Get previous values for comparison
            previous_values = type(self).objects.filter(pk=self.pk).values(*text_fields).first()
            if previous_values:
                for field_name in text_fields:
                    current_value = getattr(self, field_name)
                    # Only clean if value changed and contains \r
                    if current_value != previous_values[field_name] and "\r" in current_value:
                        remove_carriage_returns(field_name)
        else:
            # New instance - clean all fields
            for field_name in text_fields:
                remove_carriage_returns(field_name)
        super().save(*args, **kwargs)

    @property
    def formatted_data(self):
        """
        Get formatted data dictionary for API responses.

        Returns a dictionary containing all evaluation data in a
        structured format suitable for JSON serialization.
        Ensures surface and deep corrections always have proper structure
        with comments arrays, even when empty.

        Returns:
            dict: Dictionary with essay data, corrections, and score
        """
        # Ensure surface correction has proper structure with comments array
        surface_data = self.surface_correction or {}
        if not isinstance(surface_data, dict):
            surface_data = {}
        if "comments" not in surface_data:
            surface_data = {**surface_data, "comments": []}
        elif not isinstance(surface_data.get("comments"), list):
            surface_data = {**surface_data, "comments": []}

        # Ensure deep correction has proper structure
        deep_data = self.deep_correction or {}
        if not isinstance(deep_data, dict):
            deep_data = {}
        if "micro_comments" not in deep_data:
            deep_data = {**deep_data, "micro_comments": []}
        elif not isinstance(deep_data.get("micro_comments"), list):
            deep_data = {**deep_data, "micro_comments": []}
        if "macro_comments" not in deep_data:
            deep_data = {**deep_data, "macro_comments": []}
        elif not isinstance(deep_data.get("macro_comments"), list):
            deep_data = {**deep_data, "macro_comments": []}

        return {
            "essay_prompt": self.essay_prompt,
            "essay_text": self.essay_text,
            "essay_text_corrected": self.essay_text_corrected,
            "surface": surface_data,
            "deep": deep_data,
            "score": self.score,
        }

    @classmethod
    def get_usage_count(cls, user) -> int:
        """
        Calculate the number of evaluations made by this user today.

        Counts all evaluations with valid statuses (PENDING, PROCESSING, COMPLETED)
        within today's date range. Failed evaluations are not counted.

        Args:
            user: The User instance to count usage for

        Returns:
            int: Number of evaluations made today
        """
        # Get today's date range (start and end of current day)
        day_start, day_end = today_bounds_local()

        # Count requests with valid statuses within today's range
        return cls.objects.filter(
            created_by=user,
            status__in=STATUSES_FOR_LIMIT_CHECK,
            created_at__range=(day_start, day_end),
        ).count()

    @classmethod
    def is_limit_exceeded(cls, user) -> bool:
        """
        Check if the user has exceeded the daily limit for evaluations.

        If no active limit configuration exists, returns False (unlimited usage).
        Otherwise, compares current usage against the configured daily limit.

        Args:
            user: The User instance to check limits for

        Returns:
            bool: True if limit is exceeded, False otherwise
        """
        # Get the active limit configuration
        active_limit = EvaluationLimit.objects.get_active()
        if active_limit is None:
            # Missing limit config implies unlimited usage
            return False

        # Get current usage count for today
        current_usage = cls.get_usage_count(user)
        # Check if usage meets or exceeds the limit
        return current_usage >= active_limit.daily_limit
