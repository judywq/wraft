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
from .models import APIRequest
from .models import LLMModel
from .models import LLMSettings
from .signals import llm_request_completed
from .utils import mask_api_key

logger = logging.getLogger(__name__)

MyTaskModel = TypeVar("MyTaskModel", bound=APIRequest)

ApiCaller = Callable[[list[dict], float], dict]


def get_llm_caller(
    model: LLMModel,
) -> ApiCaller:
    """Get a callable that makes LLM API calls.

    Args:
        model: The LLM model to use
    Returns:
        ApiCaller: A callable that makes LLM API calls
    """

    api_key = APIKey.get_available_key(model.id, default_key=None)

    def caller(
        messages: list[dict],
        temperature: float,
    ):
        return completion(
            model=model.name,
            messages=messages,
            temperature=temperature,
            api_key=api_key,
        )

    return caller


@dataclass
class LLMRequestParams:
    request_id: int
    model_name: str
    temperature: float
    user_prompt_template: str
    system_prompt: str | None = None
    example_output: str | None = None


def call_llm_api(
    api_caller: ApiCaller,
    user_prompt: str,
    temperature: float,
    system_prompt: str | None = None,
) -> str:
    """Helper function to make LLM API calls.

    Returns:
        str: The raw response content from the model
    """

    APIKey.apply_all_keys_to_env()

    messages = [
        {"role": "user", "content": user_prompt},
    ]
    if system_prompt:
        messages.insert(0, {"role": "system", "content": system_prompt})

    response = api_caller(
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


@shared_task(bind=True)
def process_llm_request_async(
    self,
    api_request_id: int,
    delay_seconds=0,
    example_output: str | None = None,
):
    logger.info("Processing LLM request %s", api_request_id)
    if delay_seconds > 0:
        msg = f"Delaying LLM request by {delay_seconds} seconds"
        logger.info(msg)
        time.sleep(delay_seconds)

    try:
        try:
            api_request = APIRequest.objects.get(id=api_request_id)
            api_request.started_at = timezone.now()
            api_request.save()
        except APIRequest.DoesNotExist as e:
            try:
                self.retry(countdown=2**self.request.retries)
            except MaxRetriesExceededError:
                msg = f"APIRequest with id {api_request_id} not found"
                logger.exception(msg)
                raise ValueError(msg) from e

        _start_task(api_request, self.request.id)

        # Format and save the user prompt
        user_prompt = api_request.user_prompt

        if _handle_debug_delay_and_fake(api_request, example_output):
            # The request is fake
            _send_signal(api_request)
            return None

        api_caller = get_llm_caller(
            model=api_request.model,
        )

        result = call_llm_api(
            api_caller=api_caller,
            user_prompt=user_prompt,
            temperature=api_request.temperature,
        )
        api_request.result = result
        _end_task(api_request, APIRequest.Status.COMPLETED)

        # Send signal that the request is completed
        _send_signal(api_request)

    except (openai.OpenAIError, KeyError, ValueError) as e:
        api_request.status = APIRequest.Status.FAILED
        api_request.error = mask_api_key(str(e))
        if e.__context__:
            api_request.error_details = mask_api_key(str(e.__context__))
        api_request.ended_at = timezone.now()
        api_request.save()
        return False
    else:
        return True


def _send_signal(api_request: APIRequest):
    llm_request_completed.send(
        sender=process_llm_request_async,
        api_request=api_request,
    )


def _start_task(item: MyTaskModel, task_id: str | None = ""):
    item.started_at = timezone.now()
    item.status = APIRequest.Status.PROCESSING
    item.task_id = task_id
    item.save()


def _end_task(
    item: MyTaskModel,
    status: Literal[APIRequest.Status.COMPLETED, APIRequest.Status.FAILED],
):
    item.ended_at = timezone.now()
    item.status = status
    item.save()


def _handle_debug_delay_and_fake(
    item: MyTaskModel,
    example_output: str | None = None,
):
    """Handle debug delay and fake requests.
    Args:
        item: The item to handle
        delay_seconds: The delay in seconds
    Returns:
        bool: True if the item was handled, False otherwise
    """

    if LLMSettings.get_settings().fake_llm_request:
        if "fail" in str(item.input_json).lower():
            item.error = "This item is a fake failure."
            item.error_details = "This is a fake error details."
            _end_task(item, APIRequest.Status.FAILED)
        else:
            item.result = example_output
            _end_task(item, APIRequest.Status.COMPLETED)
        return True
    return False


def process_llm_request(
    api_request_id: int,
    example_output: str | None = None,
    delay_seconds=0,
):
    logger.info("Processing LLM request %s", api_request_id)
    if delay_seconds > 0:
        msg = f"Delaying LLM request by {delay_seconds} seconds"
        logger.info(msg)
        time.sleep(delay_seconds)

    try:
        try:
            api_request = APIRequest.objects.get(id=api_request_id)
            api_request.started_at = timezone.now()
            api_request.save()
        except APIRequest.DoesNotExist as e:
            msg = f"APIRequest with id {api_request_id} not found"
            logger.exception(msg)
            raise ValueError(msg) from e

        _start_task(api_request)

        # Format and save the user prompt
        user_prompt = api_request.user_prompt

        if _handle_debug_delay_and_fake(api_request, example_output):
            # The request is fake
            return api_request.result

        api_caller = get_llm_caller(
            model=api_request.model,
        )

        result = call_llm_api(
            api_caller=api_caller,
            user_prompt=user_prompt,
            temperature=api_request.temperature,
        )
        api_request.result = result
        _end_task(api_request, APIRequest.Status.COMPLETED)

    except (openai.OpenAIError, KeyError, ValueError) as e:
        logger.exception("Error processing LLM request %s", api_request_id)
        api_request.status = APIRequest.Status.FAILED
        api_request.error = mask_api_key(str(e))
        if e.__context__:
            api_request.error_details = mask_api_key(str(e.__context__))
        api_request.ended_at = timezone.now()
        api_request.save()
        raise
    return result
