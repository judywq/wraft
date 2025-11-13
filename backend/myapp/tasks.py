"""
Celery tasks for essay evaluation processing.

This module provides async task functions for processing essay evaluations.
The workflow includes surface correction, ERRANT edit extraction, surface
explanation, macro correction, micro correction, and scoring. Tasks are
executed in parallel where possible and results are saved independently.
"""

import logging
import re
from collections.abc import Callable

import json_repair
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.contrib.auth import get_user_model
from django.db import models
from django.db import transaction

from backend.llm_gateway.caller import create_llm_request
from backend.llm_gateway.exceptions import LimitExceededError

from .errant_lib import get_errant_edits
from .models import EssayEvaluation
from .utils import PARAGRAPH_DELIMITER
from .utils import post_process_deep
from .utils import remove_tag

logger = logging.getLogger(__name__)
UserModel = get_user_model()

# Total number of processing tasks that must complete for an evaluation
# Tasks: surface_explain, macro_correction, micro_correction, score
TOTAL_TASK_COUNT = 4


def _get_user_or_log_error(user_id: int, task_name: str) -> UserModel | None:
    """
    Retrieve the User object or log an error if not found.

    Helper function for getting user instances in async tasks.
    Logs errors if user is not found instead of raising exceptions.

    Args:
        user_id: The ID of the user to retrieve
        task_name: Name of the task (for logging purposes)

    Returns:
        UserModel | None: The User instance, or None if not found
    """
    try:
        return UserModel.objects.get(pk=user_id)
    except UserModel.DoesNotExist:
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
    Save task results to the EssayEvaluation object atomically.

    Updates the evaluation record with task-specific results, increments
    the completed tasks counter, and marks the evaluation as COMPLETED
    when all tasks are finished. Uses database-level locking to prevent
    race conditions when multiple tasks complete simultaneously.

    Args:
        essay_evaluation_id: The ID of the EssayEvaluation to update
        update_func: Function that applies task-specific updates to the record
        task_name: Name of the task (for logging purposes)
    """
    logger.debug(
        "Saving %s results for essay_evaluation_id: %s",
        task_name,
        essay_evaluation_id,
    )
    try:
        # Use atomic transaction with row-level locking
        with transaction.atomic():
            # Lock the row to prevent concurrent updates
            evaluation_record = EssayEvaluation.objects.select_for_update().get(
                id=essay_evaluation_id,
            )

            # Apply task-specific updates (e.g., save surface correction data)
            update_func(evaluation_record)

            # Increment completed tasks counter atomically
            evaluation_record.completed_tasks = models.F("completed_tasks") + 1
            evaluation_record.save()

            # Check if all tasks are completed
            evaluation_record.refresh_from_db()
            if evaluation_record.completed_tasks >= TOTAL_TASK_COUNT:
                # Mark evaluation as completed when all tasks finish
                evaluation_record.status = EssayEvaluation.Status.COMPLETED
                evaluation_record.save()
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
    """
    Execute the surface explanation LLM call.

    Makes an LLM request to explain surface-level corrections (grammar,
    spelling, etc.) identified by ERRANT. The LLM provides explanations
    for why each edit was made.

    Args:
        essay_text: The original essay text
        edits: List of edits from ERRANT (grammatical corrections)
        user_id: ID of the user making the request

    Returns:
        dict: Parsed JSON response with explanations for each edit
    """
    # Get user instance (or None if not found)
    current_user = _get_user_or_log_error(user_id, "run_surface_explain")

    # Prepare input data for LLM request
    input_data = {
        "essay_text": essay_text,
        "comments": edits,
    }
    # Make LLM request for surface explanations
    llm_response = create_llm_request(
        purpose="surface_explain",
        input_json=input_data,
        user=current_user,
    )
    # Parse and return JSON response (repair malformed JSON if needed)
    return json_repair.loads(llm_response)


@shared_task
def run_macro_correction(essay_prompt, essay_paragraphs_corrected, user_id):
    """Execute the macro correction LLM call."""
    current_user = _get_user_or_log_error(user_id, "run_macro_correction")

    input_data = {
        "essay_prompt": essay_prompt,
        "essay_paragraphs": essay_paragraphs_corrected,
    }
    llm_response = create_llm_request(
        purpose="macro_correction",
        input_json=input_data,
        user=current_user,
    )
    return json_repair.loads(llm_response)


@shared_task
def run_micro_correction(essay_prompt, essay_paragraphs_corrected, user_id):
    """Execute the micro correction LLM call and remove XML tags."""
    current_user = _get_user_or_log_error(user_id, "run_micro_correction")

    input_data = {
        "essay_prompt": essay_prompt,
        "essay_paragraphs": essay_paragraphs_corrected,
    }
    llm_response = create_llm_request(
        purpose="micro_correction",
        input_json=input_data,
        user=current_user,
    )
    # Remove <essay_analysis> tags from the response
    cleaned_response = remove_tag(llm_response, "</essay_analysis>")
    return json_repair.loads(cleaned_response)


@shared_task
def run_score(essay_prompt, essay_text, user_id):
    """Execute the scoring LLM call."""
    current_user = _get_user_or_log_error(user_id, "run_score")

    if current_user is None:
        return {"error": "User not found"}

    input_data = {
        "essay_prompt": essay_prompt,
        "essay_text": essay_text,
    }
    llm_response = create_llm_request(
        purpose="score",
        input_json=input_data,
        user=current_user,
    )
    return json_repair.loads(llm_response)


@shared_task
def save_surface_results(surface_explanation_data, essay_evaluation_id, edits):
    """Save surface explanation results independently."""

    def update_surface_data(evaluation_record: EssayEvaluation):
        # Merge surface explanations with edit data
        explanation_comments = surface_explanation_data.get("comments", [])
        merged_comments = []
        for edit_item in edits:
            edit_id = edit_item.get("id")
            # Match by ID, handling string/int conversion
            matching_explanations = [
                exp for exp in explanation_comments
                if str(exp.get("id")) == str(edit_id)
            ]
            explanation_reason = matching_explanations[0].get("reason", "") if matching_explanations else ""
            merged_comment = {
                **edit_item,
                "reason": explanation_reason,
            }
            merged_comments.append(merged_comment)

        surface_correction_data = {
            "comments": merged_comments,
        }
        evaluation_record.surface_correction = surface_correction_data

    _save_task_result(essay_evaluation_id, update_surface_data, "surface")


@shared_task
def save_macro_results(macro_result_data, essay_evaluation_id, essay_data):
    """Save macro correction results independently."""

    def update_macro_data(evaluation_record: EssayEvaluation):
        # Process and format macro results
        processed_macro_comments = post_process_deep(essay_data, macro_result_data, "macro")

        # Merge macro comments into deep correction data
        existing_deep_data = evaluation_record.deep_correction or {}
        updated_deep_data = {
            **existing_deep_data,
            "macro_comments": processed_macro_comments,
        }
        evaluation_record.deep_correction = updated_deep_data

    _save_task_result(essay_evaluation_id, update_macro_data, "macro")


@shared_task
def save_micro_results(micro_result_data, essay_evaluation_id, essay_data):
    """Save micro correction results independently."""

    def update_micro_data(evaluation_record: EssayEvaluation):
        # Process and format micro results
        processed_micro_comments = post_process_deep(essay_data, micro_result_data, "micro")

        # Merge micro comments into deep correction data
        existing_deep_data = evaluation_record.deep_correction or {}
        updated_deep_data = {
            **existing_deep_data,
            "micro_comments": processed_micro_comments,
        }
        evaluation_record.deep_correction = updated_deep_data

    _save_task_result(essay_evaluation_id, update_micro_data, "micro")


@shared_task
def save_score_results(score_result_data, essay_evaluation_id):
    """Save score results independently."""

    def update_score_data(evaluation_record: EssayEvaluation):
        # Extract and convert score from LLM response
        raw_score = score_result_data.get("score")
        converted_score = None
        try:
            if raw_score is not None:
                converted_score = float(raw_score)
        except (ValueError, TypeError) as exc:
            logger.warning(
                "Error converting score value '%s' to float: %s",
                raw_score,
                exc,
            )
            # Leave score as None if conversion fails
        evaluation_record.score = converted_score

    _save_task_result(essay_evaluation_id, update_score_data, "score")


@shared_task(bind=True)
def process_essay_evaluation(self, essay_evaluation_id: int):  # noqa: PLR0915
    """
    Orchestrate the essay evaluation workflow.
    Performs initial surface correction, then launches parallel tasks for
    surface explanation, macro, and micro analysis, with independent saving.
    """
    logger.info(
        "Starting process_essay_evaluation for essay_evaluation_id: %s",
        essay_evaluation_id,
    )

    try:
        evaluation_record = EssayEvaluation.objects.get(id=essay_evaluation_id)
        logger.debug("Found essay evaluation: %s", essay_evaluation_id)
    except EssayEvaluation.DoesNotExist as exc:
        try:
            self.retry(countdown=2**self.request.retries, max_retries=5)
        except MaxRetriesExceededError:
            error_msg = f"EssayEvaluation {essay_evaluation_id} not found after retries."
            logger.exception(error_msg)
            raise ValueError(error_msg) from exc

    valid_statuses = [
        EssayEvaluation.Status.PENDING,
        EssayEvaluation.Status.PROCESSING,
    ]
    if evaluation_record.status not in valid_statuses:
        logger.warning(
            "EssayEvaluation %s already processed (status: %s). Skipping.",
            essay_evaluation_id,
            evaluation_record.status,
        )
        return

    evaluation_record.status = EssayEvaluation.Status.PROCESSING
    evaluation_record.save()
    logger.debug(
        "Set status to PROCESSING for essay_evaluation_id: %s",
        essay_evaluation_id,
    )

    try:
        # Split essay text into paragraphs
        paragraph_list = [
            para.strip()
            for para in re.split(r"\n+", evaluation_record.essay_text)
            if para.strip()
        ]
        formatted_essay_text = PARAGRAPH_DELIMITER.join(paragraph_list)
        logger.debug("Processed essay paragraphs: %s", len(paragraph_list))

        essay_data_dict = {
            "essay_prompt": evaluation_record.essay_prompt,
            "essay_text": formatted_essay_text,
            "essay_paragraphs": paragraph_list,
        }
        logger.debug("Prepared essay data: %s", essay_data_dict)

        # Step 1: Surface Correction (Synchronous)
        surface_input_data = {
            "essay_paragraphs": essay_data_dict["essay_paragraphs"],
        }
        logger.debug("Surface correction input: %s", surface_input_data)

        surface_llm_response = create_llm_request(
            purpose="surface_correction",
            input_json=surface_input_data,
            user=evaluation_record.created_by,
        )
        surface_response_data = json_repair.loads(surface_llm_response)
        logger.debug("Surface correction result: %s", surface_response_data)

        essay_data_dict["essay_paragraphs_corrected"] = surface_response_data[
            "corrected_paragraphs"
        ]
        essay_data_dict["essay_text_corrected"] = PARAGRAPH_DELIMITER.join(
            surface_response_data["corrected_paragraphs"],
        )

        # Persist intermediate corrected text
        evaluation_record.essay_text_corrected = essay_data_dict["essay_text_corrected"]
        evaluation_record.save()
        logger.debug(
            "Saved corrected text for essay_evaluation_id: %s",
            essay_evaluation_id,
        )

        # Step 2: ERRANT Edits (Synchronous)
        edit_list = get_errant_edits(
            essay_data_dict["essay_text"],
            essay_data_dict["essay_text_corrected"],
        )
        logger.debug("Generated edits: %s", edit_list)

        # Steps 3, 4, 5: Parallel LLM Calls with Independent Saving
        if evaluation_record.created_by is None:
            logger.error(
                "EssayEvaluation %s is missing the 'created_by' user.",
                essay_evaluation_id,
            )
            evaluation_record.status = EssayEvaluation.Status.FAILED
            evaluation_record.save()
            return

        creator_user_id = evaluation_record.created_by.pk
        logger.debug("Using user_id: %s for LLM calls", creator_user_id)

        # Launch parallel tasks
        run_surface_explain.s(essay_data_dict["essay_text"], edit_list, creator_user_id).apply_async(
            link=save_surface_results.s(essay_evaluation_id, edit_list),
        )

        run_macro_correction.s(
            essay_data_dict["essay_prompt"],
            essay_data_dict["essay_paragraphs_corrected"],
            creator_user_id,
        ).apply_async(
            link=save_macro_results.s(essay_evaluation_id, essay_data_dict),
        )

        run_micro_correction.s(
            essay_data_dict["essay_prompt"],
            essay_data_dict["essay_paragraphs_corrected"],
            creator_user_id,
        ).apply_async(
            link=save_micro_results.s(essay_evaluation_id, essay_data_dict),
        )

        run_score.s(
            essay_data_dict["essay_prompt"],
            essay_data_dict["essay_text_corrected"],
            creator_user_id,
        ).apply_async(
            link=save_score_results.s(essay_evaluation_id),
        )

        logger.debug(
            "Successfully launched all parallel tasks for EssayEvaluation %s",
            essay_evaluation_id,
        )

    except LimitExceededError as exc:
        logger.exception(
            "Error during processing of EssayEvaluation %s",
            essay_evaluation_id,
        )
        try:
            evaluation_record.status = EssayEvaluation.Status.FAILED
            evaluation_record.error = str(exc)
            evaluation_record.save()
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
            evaluation_record.status = EssayEvaluation.Status.FAILED
            evaluation_record.error = str(exc)
            evaluation_record.save()
        except EssayEvaluation.DoesNotExist:
            logger.exception(
                "EssayEvaluation %s not found when attempting to mark as FAILED.",
                essay_evaluation_id,
            )
        raise self.retry(exc=exc, countdown=60, max_retries=3) from exc
