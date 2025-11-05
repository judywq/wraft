from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.template.defaultfilters import truncatechars

from .models import EssayEvaluation
from .models import EvaluationQuota


class EvaluationQuotaAdminForm(forms.ModelForm):
    class Meta:
        model = EvaluationQuota
        fields = ["daily_limit", "is_active"]

    def clean(self):
        cleaned_data = super().clean()
        is_active = cleaned_data.get("is_active")

        if is_active:
            # Check if another active quota exists
            existing = EvaluationQuota.objects.filter(is_active=True)
            if self.instance.pk:  # If this is an update, exclude this instance
                existing = existing.exclude(pk=self.instance.pk)

            if existing:
                raise ValidationError(
                    {
                        "is_active": "There can only be one active quota at a time. "
                        "Please deactivate the existing active quota first.",
                    },
                )

        return cleaned_data


@admin.register(EvaluationQuota)
class EvaluationQuotaAdmin(admin.ModelAdmin):
    form = EvaluationQuotaAdminForm
    list_display = ("id", "daily_limit", "is_active")
    search_fields = ("daily_limit", "is_active")


@admin.register(EssayEvaluation)
class EssayEvaluationAdmin(admin.ModelAdmin):
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
        return truncatechars(obj.essay_prompt, 100)

    @admin.display(
        description="Essay Text",
    )
    def get_essay_text(self, obj):
        return truncatechars(obj.essay_text, 100)

    @admin.display(
        description="Essay Text Corrected",
    )
    def get_essay_text_corrected(self, obj):
        return truncatechars(obj.essay_text_corrected, 100)
