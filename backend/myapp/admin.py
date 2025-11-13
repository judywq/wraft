"""
Django admin configuration for essay evaluation models.

This module provides admin interfaces for managing evaluation limits
and essay evaluations. Includes custom forms, display methods, and
validation.
"""

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.template.defaultfilters import truncatechars

from .models import EssayEvaluation
from .models import EvaluationLimit


class EvaluationLimitAdminForm(forms.ModelForm):
    """
    Custom form for EvaluationLimit admin.

    Validates that only one limit can be active at a time.
    """
    class Meta:
        model = EvaluationLimit
        fields = ["daily_limit", "is_active"]

    def clean(self):
        """
        Validate that only one active limit exists.

        Ensures that when a limit is marked as active, no other
        active limits exist. Prevents multiple active limits.

        Returns:
            dict: Cleaned form data

        Raises:
            ValidationError: If attempting to activate when another limit is active
        """
        cleaned_data = super().clean()
        is_active_flag = cleaned_data.get("is_active")

        if is_active_flag:
            # Verify no other active limit exists
            active_limits = EvaluationLimit.objects.filter(is_active=True)
            # Exclude this instance if updating (not creating)
            if self.instance.pk:
                active_limits = active_limits.exclude(pk=self.instance.pk)

            # Prevent multiple active limits
            if active_limits.exists():
                raise ValidationError(
                    {
                        "is_active": "There can only be one active limit at a time. "
                        "Please deactivate the existing active limit first.",
                    },
                )

        return cleaned_data


@admin.register(EvaluationLimit)
class EvaluationLimitAdmin(admin.ModelAdmin):
    """
    Admin interface for managing evaluation limits.

    Provides configuration for displaying and managing daily usage limits.
    Uses custom form to enforce single active limit.
    """
    form = EvaluationLimitAdminForm
    list_display = ("id", "daily_limit", "is_active")
    search_fields = ("daily_limit", "is_active")


@admin.register(EssayEvaluation)
class EssayEvaluationAdmin(admin.ModelAdmin):
    """
    Admin interface for viewing essay evaluations.

    Provides read-only access to essay evaluations with truncated
    text fields for list view. Includes filtering and search capabilities.
    """
    list_display = (
        "id",
        "status",
        "created_by",
        "score",
        "get_essay_prompt",
        "get_essay_text",
        "get_essay_text_corrected",
        "created_at",
        "updated_at",
    )
    search_fields = ("essay_prompt", "essay_text", "essay_text_corrected")
    list_filter = ("status", "created_by")
    readonly_fields = ("created_by", "created_at", "updated_at")

    @admin.display(
        description="Essay Prompt",
    )
    def get_essay_prompt(self, obj):
        """
        Display truncated essay prompt for list view.

        Args:
            obj: The EssayEvaluation instance

        Returns:
            str: Truncated prompt (max 100 characters)
        """
        return truncatechars(obj.essay_prompt, 100)

    @admin.display(
        description="Essay Text",
    )
    def get_essay_text(self, obj):
        """
        Display truncated essay text for list view.

        Args:
            obj: The EssayEvaluation instance

        Returns:
            str: Truncated text (max 100 characters)
        """
        return truncatechars(obj.essay_text, 100)

    @admin.display(
        description="Essay Text Corrected",
    )
    def get_essay_text_corrected(self, obj):
        """
        Display truncated corrected essay text for list view.

        Args:
            obj: The EssayEvaluation instance

        Returns:
            str: Truncated corrected text (max 100 characters)
        """
        return truncatechars(obj.essay_text_corrected, 100)
