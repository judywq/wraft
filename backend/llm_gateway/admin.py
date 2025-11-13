"""
Django admin configuration for LLM Gateway models.

This module provides admin interfaces for managing LLM models, configurations,
API keys, settings, and request records. It includes custom display methods,
export functionality, and permission controls.
"""

from django.contrib import admin
from django.template.defaultfilters import truncatechars
from django.utils import timezone
from django.http import HttpResponse
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from typing import Iterable, Mapping, Any
from io import BytesIO
import pandas as pd

from .models import APIKey
from .models import LLMRequestRecord
from .models import ModelConfig
from .models import LLMModel
from .models import LLMSettings
from .models import LimitConfig


def format_datetime_local(datetime_obj: timezone.datetime) -> str:
    """
    Convert a datetime object to a formatted string in local timezone.

    Formats a datetime object for display purposes, converting it to
    the local timezone and formatting as a readable string.

    Args:
        datetime_obj: The datetime object to format (can be timezone-aware
                     or timezone-naive)

    Returns:
        str: Formatted datetime string in format "YYYY-MM-DD HH:MM:SS TZ"
    """
    # Convert to local timezone if timezone-aware
    local_dt = timezone.localtime(datetime_obj)
    # Format as readable string with timezone
    return local_dt.strftime("%Y-%m-%d %H:%M:%S %Z")


def strip_illegal_excel_chars(value: Any) -> Any:
    """
    Remove illegal characters from data that cannot be used in Excel cells.

    Excel has restrictions on certain control characters. This function
    removes characters that would cause issues when exporting to Excel.

    Args:
        data: The data to clean (string or other type)

    Returns:
        str or original type: Cleaned string if input was string,
                             otherwise returns data unchanged
    """
    # Keep: If it’s a string, scrub it; otherwise pass through unchanged
    if isinstance(value, str):
        # Remove characters that Excel cannot handle
        return ILLEGAL_CHARACTERS_RE.sub("", value)
    return value


def build_excel_download(rows: Iterable[Mapping[str, Any]], filename: str) -> HttpResponse:
    """
    Generate an Excel file response from a list of row dictionaries.

    Creates an Excel file from a list of dictionaries (where each dict
    represents a row with column headers as keys). The file is prepared
    as an HTTP response for download with a timestamped filename.

    Args:
        rows: List of dictionaries, each representing a row of data.
              Dictionary keys become column headers.
        filename: Base filename for the Excel file (without extension)

    Returns:
        HttpResponse: HTTP response containing the Excel file with
                     appropriate headers for file download
    """
    # Convert list of dicts to pandas DataFrame
    frame = pd.DataFrame.from_records(rows)

    # Remove illegal characters from all cells to prevent Excel errors
    # (apply element-wise across the entire DataFrame)
    frame = frame.applymap(strip_illegal_excel_chars)

    # Generate timestamped filename
    stamp = timezone.localtime().strftime("%Y%m%d_%H%M%S")
    final_name = f"{filename}_{stamp}.xlsx"

    # Create Excel file in memory
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as xw:
        # Write DataFrame to Excel without index column
        frame.to_excel(xw, index=False)

    # Create HTTP response with Excel file
    resp = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    # Set Content-Disposition header to trigger file download
    resp["Content-Disposition"] = f'attachment; filename="{final_name}"'
    return resp


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
        "masked_key_display",
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
    def masked_key_display(self, obj):
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

    actions = ["download_as_excel"]

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

    @staticmethod
    def _resolve_field_path(root, path):
        """
        Safely walk through double-underscore paths on an object.

        Example: "created_by__name" -> obj.created_by.name
        """
        node = root
        for attr in path.split("__"):
            node = getattr(node, attr, None)
            if node is None:
                break
        return node

    @admin.action(description="Download selected rows as an Excel file")
    def download_as_excel(self, request, queryset):
        """
        Download selected LLM request records as an Excel file.

        Processes each selected record, extracts field values (including
        related fields via double underscore notation), formats datetime
        fields, and builds an Excel file for download.

        Args:
            request: The HTTP request object
            queryset: QuerySet of selected LLMRequestRecord instances

        Returns:
            HttpResponse: Excel file response for download
        """

        rows = []
        for rec in queryset:
            row = {}
            for field_path, header in self.EXPORT_COLUMNS:
                value = self._resolve_field_path(rec, field_path)

                # Datetime formatting for selected columns
                if field_path in {"created_at", "started_at", "ended_at"} and value is not None:
                    value = format_datetime_local(value)

                row[header] = value
            rows.append(row)

        # Keep the same sheet name to preserve external expectations
        return build_excel_download(rows, "llm_requests")

