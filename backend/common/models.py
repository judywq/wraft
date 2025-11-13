from django.conf import settings
from django.db import models


class CreatableBase(models.Model):
    """
    Abstract base model that adds a created_by field.

    This model tracks which user created an instance. It's an abstract model,
    meaning it won't create its own database table but provides fields to
    models that inherit from it.
    """

    # Foreign key to the user who created this instance
    # Uses SET_NULL so if the user is deleted, the reference is preserved
    # but set to NULL to maintain data integrity
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="%(class)s_created",
    )

    class Meta:
        # Abstract model - won't create a database table
        abstract = True


class TimeStampedModel(models.Model):
    """
    Abstract base model providing automatic timestamp fields.

    All models inheriting from this will automatically have created_at and
    updated_at fields that are managed by Django. This is an abstract model
    and cannot be instantiated directly.

    Usage:
        class MyModel(TimeStampedModel):
            name = models.CharField(max_length=100)
            # Automatically gets created_at and updated_at fields
    """

    # Automatically set when object is first created (only on creation)
    # This field is immutable after initial creation
    created_at = models.DateTimeField(auto_now_add=True)
    # Automatically updated whenever object is saved (on every save)
    # This includes both creation and updates
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Abstract model - won't create a database table
        abstract = True


class TaskModelBase(TimeStampedModel):
    """
    Abstract base model for task-related functionality.

    Provides common fields for tracking asynchronous task execution,
    including status, timing information, and error handling.
    Inherits timestamp fields from TimeStampedModel.

    This model is designed to work with Celery for asynchronous task processing.
    It tracks the lifecycle of a task from creation to completion or failure.
    """

    class Status(models.TextChoices):
        """
        Task status enumeration.

        Defines the possible states a task can be in during its lifecycle.
        """
        # Task created but not yet started by the worker
        PENDING = "PENDING", "Pending"
        # Task is currently being executed by a Celery worker
        PROCESSING = "PROCESSING", "Processing"
        # Task finished successfully without errors
        COMPLETED = "COMPLETED", "Completed"
        # Task failed with an error during execution
        FAILED = "FAILED", "Failed"

    # Celery task ID for tracking async task execution
    # This links the model instance to the actual Celery task
    task_id = models.CharField(max_length=255, default="", blank=True)
    # Current status of the task (one of the Status choices above)
    status = models.CharField(
        max_length=255,
        choices=Status.choices,
        default=Status.PENDING,
        blank=True,
    )
    # Timestamp when task execution started (set when worker begins processing)
    started_at = models.DateTimeField(null=True, blank=True)
    # Timestamp when task execution completed or failed (set when task finishes)
    ended_at = models.DateTimeField(null=True, blank=True)
    # User-friendly error message displayed in the UI
    # This should be a readable message that doesn't expose internal details
    error = models.TextField(
        blank=True,
        default="",
        help_text="A user-friendly error message.",
    )
    # Detailed error information for debugging purposes
    # This can include stack traces, exception details, etc.
    error_details = models.TextField(
        blank=True,
        default="",
        help_text="The detailed error information.",
    )

    class Meta:
        # Abstract model - won't create a database table
        abstract = True


# Status values that count toward daily usage limits
# Excludes FAILED status as failed requests shouldn't count against limits
# This constant is used when checking if a user has exceeded their daily
# task execution quota. Only tasks that were attempted (even if not completed)
# should count toward the limit.
STATUSES_FOR_LIMIT_CHECK = [
    TaskModelBase.Status.PENDING,
    TaskModelBase.Status.PROCESSING,
    TaskModelBase.Status.COMPLETED,
]
