from django.db import transaction

from .exceptions import QuotaExceededError
from .models import APIRequest
from .models import LLMConfig
from .models import LLMSettings
from .serializers import APIRequestSerializer
from .tasks import process_llm_request
from .tasks import process_llm_request_async


def create_llm_request(purpose, input_json, user=None, meta_data=None, background=None):
    if meta_data is None:
        meta_data = {}
    if background is None:
        background = False
    llm_config = LLMConfig.get_active_config(purpose=purpose)

    # Check quota
    has_quota = llm_config.model.check_quota(user)
    if not has_quota:
        msg = f"Daily quota exceeded for model {llm_config.model.display_name}"
        raise QuotaExceededError(msg)

    user_prompt = llm_config.user_prompt_template.format(**input_json)

    # Create request first to validate the model
    serializer = APIRequestSerializer(
        data={
            "user_prompt_template": llm_config.user_prompt_template,
            "user_prompt": user_prompt,
            "input_json": input_json,
            "model": llm_config.model.pk,
            "temperature": llm_config.temperature,
            "meta_data": meta_data,
            "created_by": user.pk if user else None,
            "status": APIRequest.Status.PENDING,
        },
    )
    serializer.is_valid(raise_exception=True)
    # Create and save the request
    api_request = serializer.save()

    delay_seconds = (
        llm_config.delay_seconds_in_fake_mode
        or LLMSettings.get_settings().task_delay_seconds
    )

    if background:
        # Ensure the actual task execution happens after transaction commit
        transaction.on_commit(
            lambda: process_llm_request_async.delay(
                api_request.id,
                delay_seconds=delay_seconds,
            ),
        )
        return api_request
    return process_llm_request(
        api_request.id,
        example_output=llm_config.example_output,
        delay_seconds=delay_seconds,
    )
