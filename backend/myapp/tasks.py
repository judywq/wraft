import logging
import re
from collections.abc import Callable

import json_repair
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.contrib.auth import get_user_model  # Import User model
from django.db import models
from django.db import transaction

from backend.llm_caller.caller import create_llm_request
from backend.llm_caller.exceptions import QuotaExceededError

from .errant_lib import get_errant_edits
from .models import EssayEvaluation
from .utils import PARAGRAPH_DELIMITER
from .utils import post_process_deep
from .utils import remove_tag

logger = logging.getLogger(__name__)
User = get_user_model()  # Get the currently active user model

TOTAL_TASKS_NUMBER = 4


def _get_user_or_log_error(user_id: int, task_name: str) -> User | None:
    """Fetches the User object or logs an error if not found."""
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.exception(
            "User with id %s not found in %s.",
            user_id,
            task_name,
        )
        return None


def _save_task_result(
    essay_evaluation_id: int,
    update_func: Callable[[EssayEvaluation], None],
    task_name: str,
) -> None:
    """
    Saves the result of a specific task to the EssayEvaluation object,
    increments the completed tasks counter, and updates the status
    if all tasks are done.
    """
    logger.debug(
        "Saving %s results for essay_evaluation_id: %s",
        task_name,
        essay_evaluation_id,
    )
    try:
        with transaction.atomic():
            essay_evaluation = EssayEvaluation.objects.select_for_update().get(
                id=essay_evaluation_id,
            )

            update_func(essay_evaluation)  # Apply task-specific updates

            essay_evaluation.completed_tasks = models.F("completed_tasks") + 1
            essay_evaluation.save()

            # Check if all tasks are completed
            essay_evaluation.refresh_from_db()
            if essay_evaluation.completed_tasks >= TOTAL_TASKS_NUMBER:
                essay_evaluation.status = EssayEvaluation.Status.COMPLETED
                essay_evaluation.save()
                logger.info(
                    "All tasks completed for essay_evaluation_id: %s",
                    essay_evaluation_id,
                )
    except EssayEvaluation.DoesNotExist:
        logger.exception(
            "EssayEvaluation %s not found when saving %s results.",
            essay_evaluation_id,
            task_name,
        )
        return


@shared_task
def run_surface_explain(essay_text, edits, user_id):
    """Runs the surface explanation LLM call."""
    user = _get_user_or_log_error(user_id, "run_surface_explain")

    surface_explain_input_json = {
        "essay_text": essay_text,
        "comments": edits,
    }
    surface_explain_result = create_llm_request(
        purpose="surface_explain",
        input_json=surface_explain_input_json,
        user=user,
    )
    return json_repair.loads(surface_explain_result)


@shared_task
def run_macro_correction(essay_prompt, essay_paragraphs_corrected, user_id):
    """Runs the macro correction LLM call."""
    user = _get_user_or_log_error(user_id, "run_macro_correction")

    macro_input_json = {
        "essay_prompt": essay_prompt,
        "essay_paragraphs": essay_paragraphs_corrected,
    }
    macro_result = create_llm_request(
        purpose="macro_correction",
        input_json=macro_input_json,
        user=user,
    )
    return json_repair.loads(macro_result)


@shared_task
def run_micro_correction(essay_prompt, essay_paragraphs_corrected, user_id):
    """Runs the micro correction LLM call and removes tags."""
    user = _get_user_or_log_error(user_id, "run_micro_correction")

    micro_input_json = {
        "essay_prompt": essay_prompt,
        "essay_paragraphs": essay_paragraphs_corrected,
    }
    micro_result = create_llm_request(
        purpose="micro_correction",
        input_json=micro_input_json,
        user=user,
    )
    # The result starts with <essay_analysis> tags, need to be removed first
    micro_result = remove_tag(micro_result, "</essay_analysis>")
    return json_repair.loads(micro_result)


@shared_task
def run_score(essay_prompt, essay_text, user_id):
    """Runs the scoring LLM call."""
    user = _get_user_or_log_error(user_id, "run_score")

    if not user:
        return {"error": "User not found"}

    score_input_json = {
        "essay_prompt": essay_prompt,
        "essay_text": essay_text,
    }
    score_result = create_llm_request(
        purpose="score",
        input_json=score_input_json,
        user=user,
    )
    return json_repair.loads(score_result)


@shared_task
def save_surface_results(surface_explanation_data, essay_evaluation_id, edits):
    """Saves surface explanation results independently."""

    def update_surface_data(essay_evaluation: EssayEvaluation):
        # Combine surface explanations with edits
        explained_comments = surface_explanation_data.get("comments", [])
        new_comments = []
        for edit in edits:
            comment_id = edit.get("id")
            # Ensure comparison works even if one is int and other is str
            c = list(
                filter(
                    lambda x: str(x.get("id")) == str(comment_id),
                    explained_comments,
                ),
            )
            reason = c[0].get("reason", "") if len(c) > 0 else ""
            new_comment = {
                **edit,
                "reason": reason,
            }
            new_comments.append(new_comment)

        surface_data = {
            "comments": new_comments,
        }
        essay_evaluation.surface_correction = surface_data

    _save_task_result(essay_evaluation_id, update_surface_data, "surface")


@shared_task
def save_macro_results(macro_result_data, essay_evaluation_id, essay_data):
    """Saves macro correction results independently."""

    def update_macro_data(essay_evaluation: EssayEvaluation):
        # Process macro results
        macro_comments = post_process_deep(essay_data, macro_result_data, "macro")

        # Update deep correction with macro comments
        current_deep_data = essay_evaluation.deep_correction or {}
        deep_data = {
            **current_deep_data,
            "macro_comments": macro_comments,
        }
        essay_evaluation.deep_correction = deep_data

    _save_task_result(essay_evaluation_id, update_macro_data, "macro")


@shared_task
def save_micro_results(micro_result_data, essay_evaluation_id, essay_data):
    """Saves micro correction results independently."""

    def update_micro_data(essay_evaluation: EssayEvaluation):
        # Process micro results
        micro_comments = post_process_deep(essay_data, micro_result_data, "micro")

        # Update deep correction with micro comments
        current_deep_data = essay_evaluation.deep_correction or {}
        deep_data = {
            **current_deep_data,
            "micro_comments": micro_comments,
        }
        essay_evaluation.deep_correction = deep_data

    _save_task_result(essay_evaluation_id, update_micro_data, "micro")


@shared_task
def save_score_results(score_result_data, essay_evaluation_id):
    """Saves score results independently."""

    def update_score_data(essay_evaluation: EssayEvaluation):
        # Process and save the score from scoring LLM
        score_value = score_result_data.get("score")
        final_score = None
        try:
            if score_value is not None:
                final_score = float(score_value)
        except (ValueError, TypeError) as e:
            logger.warning(
                "Error converting score value '%s' to float: %s",
                score_value,
                e,
            )
            # Keep score as None if conversion fails
        essay_evaluation.score = final_score

    _save_task_result(essay_evaluation_id, update_score_data, "score")


@shared_task(bind=True)
def process_essay_evaluation(self, essay_evaluation_id: int):  # noqa: PLR0915
    """
    Orchestrates the essay evaluation process.
    Performs initial surface correction, then triggers parallel tasks for
    surface explanation, macro, and micro analysis, with independent saving.
    """
    logger.info(
        "Starting process_essay_evaluation for essay_evaluation_id: %s",
        essay_evaluation_id,
    )

    try:
        essay_evaluation = EssayEvaluation.objects.get(id=essay_evaluation_id)
        logger.debug("Found essay evaluation: %s", essay_evaluation_id)
    except EssayEvaluation.DoesNotExist as e:
        try:
            self.retry(countdown=2**self.request.retries, max_retries=5)
        except MaxRetriesExceededError:
            msg = f"EssayEvaluation {essay_evaluation_id} not found after retries."
            logger.exception(msg)
            raise ValueError(msg) from e

    if essay_evaluation.status not in [
        EssayEvaluation.Status.PENDING,
        EssayEvaluation.Status.PROCESSING,
    ]:
        logger.warning(
            "EssayEvaluation %s already processed (status: %s). Skipping.",
            essay_evaluation_id,
            essay_evaluation.status,
        )
        return

    essay_evaluation.status = EssayEvaluation.Status.PROCESSING
    essay_evaluation.save()
    logger.debug(
        "Set status to PROCESSING for essay_evaluation_id: %s",
        essay_evaluation_id,
    )

    try:
        essay_paragraphs = [
            p.strip()
            for p in re.split(r"\n+", essay_evaluation.essay_text)
            if p.strip()
        ]
        essay_text = PARAGRAPH_DELIMITER.join(essay_paragraphs)
        logger.debug("Processed essay paragraphs: %s", len(essay_paragraphs))

        essay_data = {
            "essay_prompt": essay_evaluation.essay_prompt,
            "essay_text": essay_text,
            "essay_paragraphs": essay_paragraphs,
        }
        logger.debug("Prepared essay data: %s", essay_data)

        # --- Step 1: Surface Correction (Synchronous) ---
        surface_input_json = {
            "essay_paragraphs": essay_data["essay_paragraphs"],
        }
        logger.debug("Surface correction input: %s", surface_input_json)

        surface_result = create_llm_request(
            purpose="surface_correction",
            input_json=surface_input_json,
            user=essay_evaluation.created_by,
        )
        surface_result_data = json_repair.loads(surface_result)
        logger.debug("Surface correction result: %s", surface_result_data)

        essay_data["essay_paragraphs_corrected"] = surface_result_data[
            "corrected_paragraphs"
        ]
        essay_data["essay_text_corrected"] = PARAGRAPH_DELIMITER.join(
            surface_result_data["corrected_paragraphs"],
        )

        # Save intermediate corrected text
        essay_evaluation.essay_text_corrected = essay_data["essay_text_corrected"]
        essay_evaluation.save()
        logger.debug(
            "Saved corrected text for essay_evaluation_id: %s",
            essay_evaluation_id,
        )

        # --- Step 2: ERRANT Edits (Synchronous) ---
        edits = get_errant_edits(
            essay_data["essay_text"],
            essay_data["essay_text_corrected"],
        )
        logger.debug("Generated edits: %s", edits)

        # --- Step 3, 4, 5: Parallel LLM Calls with Independent Saving ---
        if not essay_evaluation.created_by:
            logger.error(
                "EssayEvaluation %s is missing the 'created_by' user.",
                essay_evaluation_id,
            )
            essay_evaluation.status = EssayEvaluation.Status.FAILED
            essay_evaluation.save()
            return

        user_id = essay_evaluation.created_by.pk
        logger.debug("Using user_id: %s for LLM calls", user_id)

        run_surface_explain.s(essay_data["essay_text"], edits, user_id).apply_async(
            link=save_surface_results.s(essay_evaluation_id, edits),
        )

        run_macro_correction.s(
            essay_data["essay_prompt"],
            essay_data["essay_paragraphs_corrected"],
            user_id,
        ).apply_async(
            link=save_macro_results.s(essay_evaluation_id, essay_data),
        )

        run_micro_correction.s(
            essay_data["essay_prompt"],
            essay_data["essay_paragraphs_corrected"],
            user_id,
        ).apply_async(
            link=save_micro_results.s(essay_evaluation_id, essay_data),
        )

        run_score.s(
            essay_data["essay_prompt"],
            essay_data["essay_text_corrected"],
            user_id,
        ).apply_async(
            link=save_score_results.s(essay_evaluation_id),
        )

        logger.debug(
            "Successfully launched all parallel tasks for EssayEvaluation %s",
            essay_evaluation_id,
        )

    except QuotaExceededError as exc:
        logger.exception(
            "Error during processing of EssayEvaluation %s",
            essay_evaluation_id,
        )
        try:
            essay_evaluation.status = EssayEvaluation.Status.FAILED
            essay_evaluation.error = str(exc)
            essay_evaluation.save()
        except EssayEvaluation.DoesNotExist:
            logger.exception(
                "EssayEvaluation %s not found when attempting to mark as FAILED.",
                essay_evaluation_id,
            )
    except Exception as exc:
        logger.exception(
            "Error during processing of EssayEvaluation %s",
            essay_evaluation_id,
        )
        try:
            essay_evaluation.status = EssayEvaluation.Status.FAILED
            essay_evaluation.error = str(exc)
            essay_evaluation.save()
        except EssayEvaluation.DoesNotExist:
            logger.exception(
                "EssayEvaluation %s not found when attempting to mark as FAILED.",
                essay_evaluation_id,
            )
        raise self.retry(exc=exc, countdown=60, max_retries=3) from exc
