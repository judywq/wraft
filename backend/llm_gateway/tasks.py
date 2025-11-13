"""
Celery tasks for processing LLM requests asynchronously.

This module provides async task functions for making LLM API calls,
handling fake mode for testing, and managing request lifecycle.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, TypeVar, cast

import openai
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.utils import timezone
from litellm import completion

from .helpers import mask_api_key
from .models import APIKey, LLMModel, LLMRequestRecord, LLMSettings
from .signals import llm_request_completed

logger = logging.getLogger(__name__)

# Type variable for task record types
TaskRecordType = TypeVar("TaskRecordType", bound=LLMRequestRecord)

# Type alias for LLM API caller function signature
LLMApiCaller = Callable[[list[dict], float], dict]


# ---------------------------
# Public API / Factories
# ---------------------------

def make_llm_caller(model: LLMModel) -> LLMApiCaller:
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
    key_for_model = APIKey.get_available_key(model.id, default_key=None)

    def _caller(messages: list[dict], temperature: float) -> dict:
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
            api_key=key_for_model,
        )

    return _caller


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


def invoke_llm(
    api_func: LLMApiCaller,
    prompt_user: str,
    temp: float,
    prompt_system: str | None = None,
) -> str:
    """
    Execute an LLM API call using the provided caller function.

    Prepares the message list (with optional system prompt), applies API keys
    to the environment, and makes the API call. Returns the text content
    from the model's response.

    Args:
        api_func: The callable function for making API calls
        prompt_user: The user's prompt text
        temp: Temperature setting for the LLM (0.0-2.0)
        prompt_system: Optional system prompt to prepend

    Returns:
        str: The raw text content from the model response
    """
    # Apply all API keys to environment variables for litellm
    APIKey.apply_all_keys_to_env()

    # Build message list starting with user prompt
    messages = _compose_messages(prompt_user, prompt_system)

    # Make the API call
    raw = api_func(messages=messages, temperature=temp)

    # Extract and return the text content from the response
    # (litellm returns OpenAI-like objects)
    return cast(str, raw.choices[0].message.content)


# ---------------------------
# Celery Tasks
# ---------------------------

@shared_task(bind=True)
def run_llm_request_task(
    self,
    request_pk: int,
    wait_s: int = 0,
    example_output: str | None = None,
):
    """
    Process an LLM request asynchronously via Celery.

    This is the main async task for processing LLM requests. It handles
    delays, fake mode, real API calls, error handling, and status updates.
    Sends a signal when the request completes.

    Args:
        self: The Celery task instance (bind=True)
        request_pk: The ID of the LLMRequestRecord to process
        wait_s: Optional delay before processing (for testing)
        example_output: Optional example output for fake mode

    Returns:
        bool: True if successful, False if failed
        None: If handled as fake request
    """
    logger.info("Processing LLM request %s", request_pk)

    # Apply delay if specified (for testing/throttling)
    _maybe_sleep(wait_s)

    request_obj: LLMRequestRecord | None = None

    try:
        # Get the request record, retrying if not found yet
        request_obj = _load_request_or_retry(self, request_pk)

        # Mark task as started
        _mark_started(request_obj, self.request.id)

        # Extract the user prompt text
        user_text = request_obj.user_prompt

        # Check if this is a fake request (for testing)
        if _maybe_fake(request_obj, example_output):
            # Fake request handled - send signal and return
            _notify_done(request_obj)
            return None

        # Get API caller function for the model
        call = make_llm_caller(model=request_obj.model)

        # Make the actual API call
        output = invoke_llm(
            api_func=call,
            prompt_user=user_text,
            temp=request_obj.temperature,
        )

        # Save the response and mark as completed
        request_obj.result = output
        _mark_finished(request_obj, LLMRequestRecord.Status.COMPLETED)

        # Notify listeners that request is completed
        _notify_done(request_obj)

    except (openai.OpenAIError, KeyError, ValueError) as exc:
        # Handle API errors and other exceptions
        _record_failure(request_obj, exc)
        return False
    else:
        return True


def run_llm_request_inline(
    request_pk: int,
    example_output: str | None = None,
    wait_s: int = 0,
) -> str:
    """
    Process an LLM request synchronously (blocking).

    This is the synchronous version of run_llm_request_task. It processes
    the request in the current thread and returns the result directly.
    Used when background processing is not needed.

    Args:
        request_pk: The ID of the LLMRequestRecord to process
        example_output: Optional example output for fake mode
        wait_s: Optional delay before processing

    Returns:
        str: The LLM response text

    Raises:
        ValueError: If the request record is not found
        openai.OpenAIError: If the API call fails
        KeyError: If response parsing fails
    """
    logger.info("Processing LLM request %s", request_pk)

    # Apply delay if specified
    _maybe_sleep(wait_s)

    request_obj = _get_request_or_throw(request_pk)

    # Mark task as started
    _mark_started(request_obj)

    # Get the user prompt text
    user_text = request_obj.user_prompt

    # Check if this is a fake request
    if _maybe_fake(request_obj, example_output):
        # Fake request - return the result
        return cast(str | None, request_obj.result) or ""

    # Obtain API caller function for the model
    call = make_llm_caller(model=request_obj.model)

    try:
        # Execute the API call
        output = invoke_llm(
            api_func=call,
            prompt_user=user_text,
            temp=request_obj.temperature,
        )

        # Save the response and mark as completed
        request_obj.result = output
        _mark_finished(request_obj, LLMRequestRecord.Status.COMPLETED)

    except (openai.OpenAIError, KeyError, ValueError) as exc:
        # Handle errors and mask API keys in error messages
        logger.exception("Error processing LLM request %s", request_pk)
        _record_failure(request_obj, exc)
        raise

    return output


# ---------------------------
# Internal Helpers
# ---------------------------

def _compose_messages(user_prompt: str, system_prompt: str | None) -> list[dict]:
    """Build message list starting with user prompt and optional system prompt."""
    msgs: list[dict] = [{"role": "user", "content": user_prompt}]
    if system_prompt:
        msgs.insert(0, {"role": "system", "content": system_prompt})
    return msgs


def _maybe_sleep(seconds: int) -> None:
    """Apply delay if specified (for testing/throttling)."""
    if seconds > 0:
        logger.info("Delaying LLM request by %s seconds", seconds)
        time.sleep(seconds)


def _load_request_or_retry(task, pk: int) -> LLMRequestRecord:
    """
    Try to load the request record; if missing, retry with exponential backoff.
    Raises ValueError once retries are exhausted.
    """
    try:
        rec = LLMRequestRecord.objects.get(id=pk)
        rec.started_at = timezone.now()
        rec.save()
        return rec
    except LLMRequestRecord.DoesNotExist as err:
        try:
            task.retry(countdown=2 ** task.request.retries)
        except MaxRetriesExceededError:
            msg = f"LLMRequestRecord with id {pk} not found"
            logger.exception(msg)
            raise ValueError(msg) from err
        # If retry scheduled, Celery will re-invoke later; return a dummy to satisfy typing.
        # (Function flow will not continue after retry.)
        raise  # pragma: no cover


def _get_request_or_throw(pk: int) -> LLMRequestRecord:
    """Simpler loader for sync code path; throws ValueError if not found."""
    try:
        rec = LLMRequestRecord.objects.get(id=pk)
        rec.started_at = timezone.now()
        rec.save()
        return rec
    except LLMRequestRecord.DoesNotExist as err:
        msg = f"LLMRequestRecord with id {pk} was not found."
        logger.exception(msg)
        raise ValueError(msg) from err


def _notify_done(api_request: LLMRequestRecord) -> None:
    """
    Send signal that an LLM request has completed.

    Notifies any registered signal handlers that the request has finished
    (either successfully or with an error).

    Args:
        api_request: The completed LLMRequestRecord instance
    """
    llm_request_completed.send(
        sender=run_llm_request_task,
        api_request=api_request,
    )


def _mark_started(record: TaskRecordType, task_id: str | None = "") -> None:
    """
    Mark a task record as started.

    Updates the record with the start time, processing status, and Celery task ID.

    Args:
        record: The task record to update
        task_id: Optional Celery task ID for tracking
    """
    record.started_at = timezone.now()
    record.status = LLMRequestRecord.Status.PROCESSING
    record.task_id = task_id or record.task_id
    record.save()


def _mark_finished(
    record: TaskRecordType,
    final_status: Literal[
        LLMRequestRecord.Status.COMPLETED, LLMRequestRecord.Status.FAILED
    ],
) -> None:
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


def _maybe_fake(
    record: TaskRecordType,
    example_output: str | None = None,
) -> bool:
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
    if not settings.fake_llm_request:
        return False

    # Check input for "fail" keyword to simulate failure
    raw_input = str(record.input_json).lower()
    if "fail" in raw_input:
        # Simulate a failed request
        record.error = "Fake Error"
        record.error_details = "Fake Error Details"
        _mark_finished(record, LLMRequestRecord.Status.FAILED)
    else:
        # Simulate a successful request with example output
        record.result = example_output
        _mark_finished(record, LLMRequestRecord.Status.COMPLETED)

    return True


def _record_failure(record: LLMRequestRecord | None, exc: Exception) -> None:
    """
    Persist failure details on the record (masking API keys) and save.
    Safe to call even if the record is None (no-op).
    """
    if record is None:
        logger.exception("Failure occurred before request record was loaded: %s", exc)
        return

    record.status = LLMRequestRecord.Status.FAILED
    # Mask API keys in error messages for security
    record.error = mask_api_key(str(exc))
    if exc.__context__:
        record.error_details = mask_api_key(str(exc.__context__))
    record.ended_at = timezone.now()
    record.save()
