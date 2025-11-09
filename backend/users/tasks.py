"""
Celery tasks for user-related operations.

This module contains asynchronous tasks that can be executed
by Celery workers for user-related operations.
"""
from celery import shared_task

from .models import User


@shared_task()
def get_users_count():
    """
    A demonstration Celery task that returns the total number of users.

    This task is provided as an example of how to create Celery tasks
    for user-related operations. It can be extended to perform more
    complex operations like user statistics, bulk operations, etc.

    Returns:
        int: Total number of users in the database
    """
    return User.objects.count()
