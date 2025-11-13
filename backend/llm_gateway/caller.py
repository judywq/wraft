"""
High-level function for creating and processing LLM requests.

This module provides the main entry point for creating LLM requests.
It handles configuration retrieval, limit checking, prompt formatting,
and request processing (synchronously or asynchronously).
"""

from django.db import transaction

from .exceptions import LimitExceededError
from .models import LLMRequestRecord
from .models import ModelConfig
from .models import LLMSettings
from .serializers import LLMRequestRecordSerializer
from .tasks import run_llm_request_inline
from .tasks import run_llm_request_task


def create_llm_request(purpose, input_json, user=None, meta_data=None, background=None):
    """
    Create and process an LLM request.

    This is the main entry point for making LLM requests. It:
    1. Retrieves the active configuration for the purpose
    2. Checks if the user has exceeded daily limits
    3. Formats the prompt template with input data
    4. Creates a request record
    5. Processes the request (synchronously or asynchronously)

    Args:
        purpose: The purpose/use case for this request (e.g., "score", "correction")
        input_json: Dictionary of input data to format into the prompt template
        user: Optional User instance making the request
        meta_data: Optional metadata dictionary to attach to the request
        background: If True, process asynchronously via Celery; if False, process synchronously

    Returns:
        LLMRequestRecord: The created request record (if background=True)
        str: The LLM response text (if background=False)

    Raises:
        LimitExceededError: If the user has exceeded their daily limit
        ValueError: If no active config exists for the purpose
    """
    # Set default values for optional parameters
    metadata_dict = meta_data if meta_data is not None else {}
    run_in_background = background if background is not None else False

    # Retrieve active configuration for the specified purpose
    # Raises ValueError if no active config exists
    active_config = ModelConfig.get_active_config(purpose=purpose)

    # Check whether user has exceeded the daily limit for this model
    limit_exceeded = active_config.model.is_limit_exceeded(user)
    if limit_exceeded:
        error_message = f"Daily limit exceeded for model {active_config.model.display_name}"
        raise LimitExceededError(error_message)

    # Format the prompt template with input data
    # Uses Python string formatting: template.format(**input_json)
    formatted_prompt = active_config.user_prompt_template.format(**input_json)

    # Prepare request data for serializer
    request_data = {
        "user_prompt_template": active_config.user_prompt_template,
        "user_prompt": formatted_prompt,
        "input_json": input_json,
        "model": active_config.model.pk,
        "temperature": active_config.temperature,
        "meta_data": metadata_dict,
        "created_by": user.pk if user else None,
        "status": LLMRequestRecord.Status.PENDING,
    }

    # Validate and create the request record
    request_serializer = LLMRequestRecordSerializer(data=request_data)
    request_serializer.is_valid(raise_exception=True)
    request_record = request_serializer.save()

    # Determine delay duration from config or global settings
    delay_duration = (
        active_config.delay_seconds_in_fake_mode
        or LLMSettings.get_settings().task_delay_seconds
    )

    if run_in_background:
        # Schedule async processing after transaction commits
        # This ensures the record is saved before the task starts
        transaction.on_commit(
            lambda: run_llm_request_task.delay(
                request_record.id,
                wait_s=delay_duration,
            ),
        )
        # Return the record immediately (processing happens in background)
        return request_record

    # Process synchronously and return the response text
    return run_llm_request_inline(
        request_record.id,
        example_output=active_config.example_output,
        wait_s=delay_duration,
    )
