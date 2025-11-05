from django.contrib import admin
from django.template.defaultfilters import truncatechars

from .models import APIKey
from .models import APIRequest
from .models import LLMConfig
from .models import LLMModel
from .models import LLMSettings
from .models import QuotaConfig
from .utils import format_datetime
from .utils import generate_excel_response


@admin.register(QuotaConfig)
class QuotaConfigAdmin(admin.ModelAdmin):
    list_display = ["model", "daily_limit", "created_at", "updated_at"]
    list_filter = ["model"]


@admin.register(APIRequest)
class APIRequestAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "status",
        "get_model_name",
        "temperature",
        "get_user_prompt",
        "get_input_json",
        "get_result",
        "get_error_message",
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

    actions = ["export_as_excel"]

    # Define field mapping for export
    export_field_mapping = [
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
    def get_model_name(self, obj):
        return obj.model.display_name

    @admin.display(description="User Prompt")
    def get_user_prompt(self, obj):
        return truncatechars(obj.user_prompt, 100)

    @admin.display(description="Input JSON")
    def get_input_json(self, obj):
        return truncatechars(obj.input_json, 100)

    @admin.display(description="Result")
    def get_result(self, obj):
        return truncatechars(obj.result, 100)

    @admin.display(description="Error Message")
    def get_error_message(self, obj):
        return truncatechars(obj.error, 100)

    def has_add_permission(self, request):
        """Disable add permission for APIRequestAdmin"""
        return False

    @admin.action(description="Export selected requests as Excel")
    def export_as_excel(self, request, queryset):
        rows = []
        # Write data rows
        for obj in queryset:
            row = {}
            for field, header in self.export_field_mapping:
                value = obj
                for attr in field.split("__"):
                    value = getattr(value, attr, None)
                    if value is None:
                        break

                # Format the value if it's a datetime field
                if (
                    field in ["created_at", "started_at", "ended_at"]
                    and value is not None
                ):
                    value = format_datetime(value)

                row.update({header: value})
            rows.append(row)
        return generate_excel_response(rows, "Evaluations")


@admin.register(LLMModel)
class LLMModelAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "display_name",
        "name",
        "url",
        "order",
        "is_default",
        "is_active",
        "created_at",
        "updated_at",
    ]
    list_filter = ["is_active", "is_default"]
    search_fields = ["name", "display_name"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "display_name",
                    "name",
                    "url",
                ),
            },
        ),
        (
            "Settings",
            {
                "fields": (
                    "order",
                    "is_default",
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


@admin.register(LLMConfig)
class LLMConfigAdmin(admin.ModelAdmin):
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


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
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
        """Show only the last 4 characters of the key."""
        return f"{obj.key[:4]}...{obj.key[-4:]}" if obj.key else ""


@admin.register(LLMSettings)
class LLMSettingsAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "fake_llm_request",
        "task_delay_seconds",
        "created_at",
        "updated_at",
    ]
    readonly_fields = ["created_at", "updated_at"]

    def has_add_permission(self, request):
        """Only allow adding if no settings exist."""
        return not LLMSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of settings."""
        return False
