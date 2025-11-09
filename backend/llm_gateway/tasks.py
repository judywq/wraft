"""
Celery tasks for processing LLM requests asynchronously.

This module provides async task functions for making LLM API calls,
handling fake mode for testing, and managing request lifecycle.
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal
from typing import TypeVar

import openai
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.utils import timezone
from litellm import completion

from .models import APIKey
from .models import LLMRequestRecord
from .models import LLMModel
from .models import LLMSettings
from .signals import llm_request_completed
from .helpers import mask_api_key

logger = logging.getLogger(__name__)

# Type variable for task record types
TaskRecordType = TypeVar("TaskRecordType", bound=LLMRequestRecord)

# Type alias for LLM API caller function signature
LLMApiCaller = Callable[[list[dict], float], dict]


def get_llm_gateway(
    model: LLMModel,
) -> LLMApiCaller:
    """
    Retrieve a callable function for making LLM API calls.

    Creates and returns a configured API caller function for the specified model.
    The caller function uses the model's API key and name to make requests
    via the litellm library.

    Args:
        model: The LLM model instance to use for API calls

    Returns:
        LLMApiCaller: A callable function that executes LLM API calls.
                     Takes (messages, temperature) and returns API response.
    """
    # Get the API key for this model (or None if not found)
    model_api_key = APIKey.get_available_key(model.id, default_key=None)

    def api_caller(
        messages: list[dict],
        temperature: float,
    ):
        """
        Execute an LLM API call using litellm.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Temperature setting for the LLM (0.0-2.0)

        Returns:
            dict: The API response from litellm
        """
        return completion(
            model=model.name,
            messages=messages,
            temperature=temperature,
            api_key=model_api_key,
        )

    return api_caller


@dataclass
class LLMRequestParams:
    """
    Data class for LLM request parameters.

    Stores the parameters needed to make an LLM API call, including
    the request ID, model configuration, and prompt information.
    """
    request_id: int  # ID of the LLMRequestRecord
    model_name: str  # Name of the LLM model to use
    temperature: float  # Temperature setting (0.0-2.0)
    user_prompt_template: str  # Prompt template to format
    system_prompt: str | None = None  # Optional system prompt
    example_output: str | None = None  # Optional example output for fake mode


def call_llm_api(
    api_caller: LLMApiCaller,
    user_prompt: str,
    temperature: float,
    system_prompt: str | None = None,
) -> str:
    """
    Execute an LLM API call using the provided caller function.

    Prepares the message list (with optional system prompt), applies API keys
    to the environment, and makes the API call. Returns the text content
    from the model's response.

    Args:
        api_caller: The callable function for making API calls
        user_prompt: The user's prompt text
        temperature: Temperature setting for the LLM (0.0-2.0)
        system_prompt: Optional system prompt to prepend

    Returns:
        str: The raw text content from the model response
    """
    # Apply all API keys to environment variables for litellm
    APIKey.apply_all_keys_to_env()

    # Build message list starting with user prompt
    message_list = [
        {"role": "user", "content": user_prompt},
    ]
    # Add system prompt at the beginning if provided
    if system_prompt:
        message_list.insert(0, {"role": "system", "content": system_prompt})

    # Make the API call
    api_response = api_caller(
        messages=message_list,
        temperature=temperature,
    )
    # Extract and return the text content from the response
    return api_response.choices[0].message.content


@shared_task(bind=True)
def process_llm_request_async(
    self,
    api_request_id: int,
    delay_seconds=0,
    example_output: str | None = None,
):
    """
    Process an LLM request asynchronously via Celery.

    This is the main async task for processing LLM requests. It handles
    delays, fake mode, real API calls, error handling, and status updates.
    Sends a signal when the request completes.

    Args:
        self: The Celery task instance (bind=True)
        api_request_id: The ID of the LLMRequestRecord to process
        delay_seconds: Optional delay before processing (for testing)
        example_output: Optional example output for fake mode

    Returns:
        bool: True if successful, False if failed
        None: If handled as fake request
    """
    logger.info("Processing LLM request %s", api_request_id)
    # Apply delay if specified (for testing/throttling)
    if delay_seconds > 0:
        log_msg = f"Delaying LLM request by {delay_seconds} seconds"
        logger.info(log_msg)
        time.sleep(delay_seconds)

    try:
        # Get the request record, retrying if not found yet
        try:
            request_record = LLMRequestRecord.objects.get(id=api_request_id)
            request_record.started_at = timezone.now()
            request_record.save()
        except LLMRequestRecord.DoesNotExist as exc:
            # Retry with exponential backoff if record doesn't exist yet
            try:
                self.retry(countdown=2**self.request.retries)
            except MaxRetriesExceededError:
                error_msg = f"LLMRequestRecord with id {api_request_id} not found"
                logger.exception(error_msg)
                raise ValueError(error_msg) from exc

        # Mark task as started
        _start_task(request_record, self.request.id)

        # Extract the user prompt text
        prompt_text = request_record.user_prompt

        # Check if this is a fake request (for testing)
        if _handle_debug_delay_and_fake(request_record, example_output):
            # Fake request handled - send signal and return
            _send_signal(request_record)
            return None

        # Get API caller function for the model
        llm_caller = get_llm_gateway(
            model=request_record.model,
        )

        # Make the actual API call
        response_text = call_llm_api(
            api_caller=llm_caller,
            user_prompt=prompt_text,
            temperature=request_record.temperature,
        )
        # Save the response and mark as completed
        request_record.result = response_text
        _end_task(request_record, LLMRequestRecord.Status.COMPLETED)

        # Notify listeners that request is completed
        _send_signal(request_record)

    except (openai.OpenAIError, KeyError, ValueError) as exc:
        # Handle API errors and other exceptions
        request_record.status = LLMRequestRecord.Status.FAILED
        # Mask API keys in error messages for security
        request_record.error = mask_api_key(str(exc))
        if exc.__context__:
            request_record.error_details = mask_api_key(str(exc.__context__))
        request_record.ended_at = timezone.now()
        request_record.save()
        return False
    else:
        return True


def _send_signal(api_request: LLMRequestRecord):
    """
    Send signal that an LLM request has completed.

    Notifies any registered signal handlers that the request has finished
    (either successfully or with an error).

    Args:
        api_request: The completed LLMRequestRecord instance
    """
    llm_request_completed.send(
        sender=process_llm_request_async,
        api_request=api_request,
    )


def _start_task(record: TaskRecordType, task_id: str | None = ""):
    """
    Mark a task record as started.

    Updates the record with the start time, processing status, and Celery task ID.

    Args:
        record: The task record to update
        task_id: Optional Celery task ID for tracking
    """
    record.started_at = timezone.now()
    record.status = LLMRequestRecord.Status.PROCESSING
    record.task_id = task_id
    record.save()


def _end_task(
    record: TaskRecordType,
    final_status: Literal[LLMRequestRecord.Status.COMPLETED, LLMRequestRecord.Status.FAILED],
):
    """
    Mark a task record as completed or failed.

    Updates the record with the end time and final status.

    Args:
        record: The task record to update
        final_status: Either COMPLETED or FAILED status
    """
    record.ended_at = timezone.now()
    record.status = final_status
    record.save()


def _handle_debug_delay_and_fake(
    record: TaskRecordType,
    example_output: str | None = None,
):
    """
    Process fake requests for debugging purposes.

    If fake mode is enabled in settings, returns fake responses instead
    of making real API calls. Can simulate both success and failure cases.

    Args:
        record: The request record to handle
        example_output: Optional example output to use as fake response

    Returns:
        bool: True if handled as fake request, False if real request needed
    """
    # Get global settings
    settings = LLMSettings.get_settings()
    # Check if fake mode is enabled
    if settings.fake_llm_request:
        # Check input for "fail" keyword to simulate failure
        input_str = str(record.input_json).lower()
        if "fail" in input_str:
            # Simulate a failed request
            record.error = "Fake Error"
            record.error_details = "Fake Error Details"
            _end_task(record, LLMRequestRecord.Status.FAILED)
        else:
            # Simulate a successful request with example output
            record.result = example_output
            _end_task(record, LLMRequestRecord.Status.COMPLETED)
        return True
    return False


def process_llm_request(
    api_request_id: int,
    example_output: str | None = None,
    delay_seconds=0,
):
    """
    Process an LLM request synchronously (blocking).

    This is the synchronous version of process_llm_request_async. It processes
    the request in the current thread and returns the result directly.
    Used when background processing is not needed.

    Args:
        api_request_id: The ID of the LLMRequestRecord to process
        example_output: Optional example output for fake mode
        delay_seconds: Optional delay before processing

    Returns:
        str: The LLM response text

    Raises:
        ValueError: If the request record is not found
        openai.OpenAIError: If the API call fails
        KeyError: If response parsing fails
    """
    logger.info("Processing LLM request %s", api_request_id)
    # Apply delay if specified
    if delay_seconds > 0:
        log_msg = f"Delaying LLM request by {delay_seconds} seconds."
        logger.info(log_msg)
        time.sleep(delay_seconds)

    try:
        # Get the request record
        try:
            request_record = LLMRequestRecord.objects.get(id=api_request_id)
            request_record.started_at = timezone.now()
            request_record.save()
        except LLMRequestRecord.DoesNotExist as exc:
            error_msg = f"LLMRequestRecord with id {api_request_id} was not found."
            logger.exception(error_msg)
            raise ValueError(error_msg) from exc

        # Mark task as started
        _start_task(request_record)

        # Get the user prompt text
        prompt_text = request_record.user_prompt

        # Check if this is a fake request
        if _handle_debug_delay_and_fake(request_record, example_output):
            # Fake request - return the result
            return request_record.result

        # Obtain API caller function for the model
        llm_caller = get_llm_gateway(
            model=request_record.model,
        )

        # Execute the API call
        response_text = call_llm_api(
            api_caller=llm_caller,
            user_prompt=prompt_text,
            temperature=request_record.temperature,
        )
        # Save the response and mark as completed
        request_record.result = response_text
        _end_task(request_record, LLMRequestRecord.Status.COMPLETED)

    except (openai.OpenAIError, KeyError, ValueError) as exc:
        # Handle errors and mask API keys in error messages
        logger.exception("Error processing LLM request %s", api_request_id)
        request_record.status = LLMRequestRecord.Status.FAILED
        request_record.error = mask_api_key(str(exc))
        if exc.__context__:
            request_record.error_details = mask_api_key(str(exc.__context__))
        request_record.ended_at = timezone.now()
        request_record.save()
        raise
    return response_text
