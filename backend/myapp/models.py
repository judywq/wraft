from django.core.exceptions import ValidationError
from django.db import models

from backend.core.models import CreatableBase
from backend.core.models import TaskTimestampedBase
from backend.llm_caller.utils import get_today_date_range

QUOTA_USAGE_STATUS = [
    TaskTimestampedBase.Status.PENDING,
    TaskTimestampedBase.Status.PROCESSING,
    TaskTimestampedBase.Status.COMPLETED,
]


class EvaluationQuotaManager(models.Manager):
    def get_active(self):
        """Return the currently active quota, or None if none exists."""
        try:
            return self.get(is_active=True)
        except (EvaluationQuota.DoesNotExist, EvaluationQuota.MultipleObjectsReturned):
            return None


class EvaluationQuota(models.Model):
    daily_limit = models.IntegerField(
        default=10,
        help_text="Maximum number of requests per day.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the quota is active.",
    )
    objects = EvaluationQuotaManager()

    class Meta:
        get_latest_by = "created_at"
        verbose_name = "Quota"
        verbose_name_plural = "Quotas"

    def __str__(self):
        return f"EvaluationQuota(limit={self.daily_limit})"

    def save(self, *args, **kwargs):
        if self.is_active:
            # Check if there's already an active quota that isn't this instance
            existing = EvaluationQuota.objects.filter(is_active=True)
            if self.pk:  # If this is an update, exclude this instance
                existing = existing.exclude(pk=self.pk)

            if existing.exists():
                msg = "There can only be one active quota at a time."
                raise ValidationError(msg)
        super().save(*args, **kwargs)


class EssayEvaluation(TaskTimestampedBase, CreatableBase):
    essay_prompt = models.TextField(
        max_length=1000,
        default="",
        blank=True,
        help_text="The prompt for the essay.",
    )
    essay_text = models.TextField(
        max_length=5000,
        blank=False,
        help_text="The essay text.",
    )
    essay_text_corrected = models.TextField(
        max_length=5000,
        default="",
        blank=True,
        help_text="The corrected essay text.",
    )
    surface_correction = models.JSONField(
        default=dict,
        blank=True,
        help_text="The surface level correction of the essay.",
    )
    deep_correction = models.JSONField(
        default=dict,
        blank=True,
        help_text="The deep level correction of the essay.",
    )
    score = models.FloatField(
        null=True,
        blank=True,
        help_text="The score of the essay.",
    )
    completed_tasks = models.IntegerField(
        default=0,
        help_text="Number of completed processing tasks.",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Usage"
        verbose_name_plural = "Usages"

    def __str__(self):
        return f"Essay Evaluation for {self.essay_text[:10]}..."

    def save(self, *args, **kwargs):
        # only clean fields when they've changed or contain carriage returns
        fields = ["essay_prompt", "essay_text", "essay_text_corrected"]

        def clean_field(field):
            if "\r" in getattr(self, field):
                setattr(self, field, getattr(self, field).replace("\r", ""))

        if self.pk:
            old = type(self).objects.filter(pk=self.pk).values(*fields).first()
            if old:
                for f in fields:
                    val = getattr(self, f)
                    if val != old[f] and "\r" in val:
                        clean_field(f)
        else:
            for f in fields:
                clean_field(f)
        super().save(*args, **kwargs)

    @property
    def formatted_data(self):
        return {
            "essay_prompt": self.essay_prompt,
            "essay_text": self.essay_text,
            "essay_text_corrected": self.essay_text_corrected,
            "surface": self.surface_correction,
            "deep": self.deep_correction,
            "score": self.score,
        }

    @classmethod
    def get_used_quota(cls, user) -> int:
        """Get the number of completed requests for today for this user."""
        today_start, today_end = get_today_date_range()

        # Calculate the number of completed requests for today
        # status is either PENDING or COMPLETED
        return cls.objects.filter(
            created_by=user,
            status__in=QUOTA_USAGE_STATUS,
            created_at__range=(today_start, today_end),
        ).count()

    @classmethod
    def check_quota(cls, user) -> bool:
        """
        Check if the user still has enough quota
        Returns True if the user has remaining quota
                False if the user has exceeded their quota.
        """
        quota_config = EvaluationQuota.objects.get_active()
        if not quota_config:
            # No active quota config means unlimited requests
            return True

        used_quota = cls.get_used_quota(user)
        return used_quota < quota_config.daily_limit
