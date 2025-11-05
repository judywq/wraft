from django.conf import settings
from django.db import models


class TimestampedBase(models.Model):
    """Base model that adds created_at and updated_at timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TaskTimestampedBase(TimestampedBase):
    """Base model that adds task-related fields and timestamps."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        ABORTED = "ABORTED", "Aborted"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
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

    task_id = models.CharField(max_length=100, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class CreatableBase(models.Model):
    """
    Abstract base model that adds a created_by field.
    """

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="%(class)s_created",
    )

    class Meta:
        abstract = True
