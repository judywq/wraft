"""
Django admin configuration for LLM Gateway models.

This module provides admin interfaces for managing LLM models, configurations,
API keys, settings, and request records. It includes custom display methods,
export functionality, and permission controls.
"""

from django.contrib import admin
from django.template.defaultfilters import truncatechars

from .models import APIKey
from .models import LLMRequestRecord
from .models import ModelConfig
from .models import LLMModel
from .models import LLMSettings
from .models import LimitConfig
from .helpers import format_datetime
from .helpers import generate_excel_response


@admin.register(LLMModel)
class LLMModelAdmin(admin.ModelAdmin):
    """
    Admin interface for managing LLM models.

    Provides configuration for displaying, filtering, and searching LLM models
    in the Django admin panel. Models are ordered by their display order.
    """
    list_display = [
        "id",
        "display_name",
        "name",
        "order",
        "is_active",
        "created_at",
        "updated_at",
    ]
    list_filter = ["is_active",]
    search_fields = ["name", "display_name"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "display_name",
                    "name",
                ),
            },
        ),
        (
            "Settings",
            {
                "fields": (
                    "order",
                    "is_active",
                ),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )
    ordering = ["order"]


@admin.register(ModelConfig)
class ModelConfigAdmin(admin.ModelAdmin):
    """
    Admin interface for managing model configurations.

    ModelConfig links LLM models to specific purposes (e.g., scoring, correction)
    with custom prompt templates, temperature settings, and example outputs.
    """
    list_display = [
        "purpose",
        "model",
        "is_active",
        "user_prompt_template",
        "temperature",
        "example_output",
        "delay_seconds_in_fake_mode",
        "updated_at",
    ]
    list_filter = ["model", "is_active", "created_at"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(LimitConfig)
class LimitConfigAdmin(admin.ModelAdmin):
    """
    Admin interface for managing daily usage limits per model.

    Each LimitConfig defines the maximum number of requests allowed per day
    for a specific LLM model.
    """
    list_display = ["model", "daily_limit", "created_at", "updated_at"]
    list_filter = ["model"]


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    """
    Admin interface for managing API keys for LLM providers.

    API keys are stored securely and displayed in a masked format in the admin
    panel. Keys can be associated with specific models or used globally.
    """
    list_display = [
        "id",
        "model",
        "name",
        "masked_key",
        "is_active",
        "created_at",
        "updated_at",
    ]
    list_filter = ["is_active", "model"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["created_at"]

    @admin.display(
        description="API Key",
    )
    def masked_key(self, obj):
        """
        Display the API key in a masked format for security.

        Shows the first 10 characters and last 4 characters, with asterisks
        in between to prevent full key exposure in the admin interface.

        Args:
            obj: The APIKey instance

        Returns:
            str: Masked key string (e.g., "sk-1234567890********abcd")
        """
        return f"{obj.key[:10]}********{obj.key[-4:]}" if obj.key else ""


@admin.register(LLMSettings)
class LLMSettingsAdmin(admin.ModelAdmin):
    """
    Admin interface for global LLM gateway settings.

    Implements a singleton pattern - only one settings instance can exist.
    Settings control fake mode (for testing) and task delays.
    """
    list_display = [
        "id",
        "fake_llm_request",
        "task_delay_seconds",
        "created_at",
        "updated_at",
    ]
    readonly_fields = ["created_at", "updated_at"]

    def has_add_permission(self, request):
        """
        Restrict creation to only when no settings instance exists.

        Enforces singleton pattern by preventing multiple settings instances.

        Args:
            request: The HTTP request object

        Returns:
            bool: True if no settings exist, False otherwise
        """
        return not LLMSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """
        Prevent deletion of the settings instance.

        Ensures the singleton settings object cannot be accidentally deleted.

        Args:
            request: The HTTP request object
            obj: Optional settings instance (unused)

        Returns:
            bool: Always False to prevent deletion
        """
        return False


@admin.register(LLMRequestRecord)
class LLMRequestRecordAdmin(admin.ModelAdmin):
    """
    Admin interface for viewing and exporting LLM request records.

    Request records are created automatically by the system and cannot be
    manually created through the admin. This interface provides read-only
    access and export functionality for analysis and debugging.
    """
    list_display = [
        "id",
        "status",
        "model_display",
        "temperature",
        "prompt_display",
        "input_display",
        "result_display",
        "error_display",
        "created_at",
        "started_at",
        "ended_at",
    ]
    list_filter = ["status", "model"]
    search_fields = [
        "input_json",
        "result",
    ]
    readonly_fields = ["created_at", "updated_at", "started_at", "ended_at", "task_id"]

    actions = ["export_to_excel"]

    # Mapping of database field paths to Excel column headers for export
    FIELD_MAPPING_FOR_EXPORT = [
        ("id", "ID"),
        ("status", "Status"),
        ("created_by__name", "User Name"),
        ("created_by__email", "User Email"),
        ("model__name", "LLM Model"),
        ("input_json", "Input JSON"),
        ("result", "Raw Response"),
        ("user_prompt", "User Prompt"),
        ("error", "Error"),
        ("created_at", "Created At"),
        ("started_at", "Started At"),
        ("ended_at", "Ended At"),
    ]

    @admin.display(description="Model", ordering="model__display_name")
    def model_display(self, obj):
        """
        Display the human-readable model name.

        Args:
            obj: The LLMRequestRecord instance

        Returns:
            str: The display name of the associated model
        """
        return obj.model.display_name

    @admin.display(description="User Prompt")
    def prompt_display(self, obj):
        """
        Display truncated user prompt for list view.

        Args:
            obj: The LLMRequestRecord instance

        Returns:
            str: Truncated prompt (max 100 characters)
        """
        return truncatechars(obj.user_prompt, 100)

    @admin.display(description="Input JSON")
    def input_display(self, obj):
        """
        Display truncated input JSON for list view.

        Args:
            obj: The LLMRequestRecord instance

        Returns:
            str: Truncated JSON string (max 100 characters)
        """
        return truncatechars(obj.input_json, 100)

    @admin.display(description="Result")
    def result_display(self, obj):
        """
        Display truncated LLM response for list view.

        Args:
            obj: The LLMRequestRecord instance

        Returns:
            str: Truncated result text (max 100 characters)
        """
        return truncatechars(obj.result, 100)

    @admin.display(description="Error Message")
    def error_display(self, obj):
        """
        Display truncated error message for list view.

        Args:
            obj: The LLMRequestRecord instance

        Returns:
            str: Truncated error text (max 100 characters)
        """
        return truncatechars(obj.error, 100)

    def has_add_permission(self, request):
        """
        Prevent manual creation of request records.

        Records are created automatically by the system when LLM requests
        are made. Manual creation is disabled to maintain data integrity.

        Args:
            request: The HTTP request object

        Returns:
            bool: Always False to prevent manual creation
        """
        return False

    @admin.action(description="Export selected requests as Excel")
    def export_to_excel(self, request, queryset):
        """
        Export selected LLM request records to an Excel file.

        Processes each selected record, extracts field values (including
        related fields via double underscore notation), formats datetime
        fields, and generates an Excel file for download.

        Args:
            request: The HTTP request object
            queryset: QuerySet of selected LLMRequestRecord instances

        Returns:
            HttpResponse: Excel file download response
        """
        export_rows = []
        # Process each selected record
        for record in queryset:
            row_data = {}
            # Extract field values using field path mapping
            for field_path, column_header in self.FIELD_MAPPING_FOR_EXPORT:
                field_value = record
                # Navigate through related fields using double underscore notation
                # (e.g., "created_by__name" accesses record.created_by.name)
                for attr_name in field_path.split("__"):
                    field_value = getattr(field_value, attr_name, None)
                    if field_value is None:
                        break

                # Apply datetime formatting when needed for better readability
                if (
                    field_path in ["created_at", "started_at", "ended_at"]
                    and field_value is not None
                ):
                    field_value = format_datetime(field_value)

                row_data.update({column_header: field_value})
            export_rows.append(row_data)
        return generate_excel_response(export_rows, "Evaluations")
