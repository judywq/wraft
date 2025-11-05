import pytest
from django.core.exceptions import ValidationError

from backend.myapp.models import EssayEvaluation
from backend.myapp.models import EvaluationQuota


@pytest.mark.django_db
def test_new_instance_cleans_carriage_returns():
    prompt = "This is\r a test\r"
    text = "Line1\rLine2"
    corrected = "\rCorrected\rText"
    essay_eval = EssayEvaluation(
        essay_prompt=prompt,
        essay_text=text,
        essay_text_corrected=corrected,
    )
    essay_eval.save()
    essay_eval.refresh_from_db()
    # All carriage returns should be removed on new save
    assert "\r" not in essay_eval.essay_prompt
    assert essay_eval.essay_prompt == prompt.replace("\r", "")
    assert "\r" not in essay_eval.essay_text
    assert essay_eval.essay_text == text.replace("\r", "")
    assert "\r" not in essay_eval.essay_text_corrected
    assert essay_eval.essay_text_corrected == corrected.replace("\r", "")


@pytest.mark.django_db
def test_update_cleans_only_changed_field():
    # Create initial instance without carriage returns
    essay_eval = EssayEvaluation(
        essay_prompt="Initial prompt",
        essay_text="Initial text",
        essay_text_corrected="Initial corrected",
    )
    essay_eval.save()
    essay_eval.refresh_from_db()

    original_prompt = essay_eval.essay_prompt
    original_corrected = essay_eval.essay_text_corrected

    # Update only essay_text with carriage returns
    new_text = "Updated\r text\r"
    essay_eval.essay_text = new_text
    essay_eval.save()
    essay_eval.refresh_from_db()

    # Only essay_text should have been cleaned and updated
    assert essay_eval.essay_text == new_text.replace("\r", "")
    assert essay_eval.essay_prompt == original_prompt
    assert essay_eval.essay_text_corrected == original_corrected


@pytest.mark.django_db
def test_update_without_carriage_returns_leaves_fields_intact():
    # Create initial instance
    essay_eval = EssayEvaluation(
        essay_prompt="Prompt",
        essay_text="Text",
        essay_text_corrected="Corrected",
    )
    essay_eval.save()
    essay_eval.refresh_from_db()

    # Update a field without carriage returns
    essay_eval.essay_prompt = "New prompt without cr"
    essay_eval.save()
    essay_eval.refresh_from_db()

    # Ensure no unintended modifications
    assert essay_eval.essay_prompt == "New prompt without cr"
    assert essay_eval.essay_text == "Text"
    assert essay_eval.essay_text_corrected == "Corrected"


@pytest.mark.django_db
def test_only_one_active_quota_allowed():
    # Create first active quota
    quota1 = EvaluationQuota(daily_limit=10, is_active=True)
    quota1.save()

    # Try to create second active quota
    quota2 = EvaluationQuota(daily_limit=20, is_active=True)
    with pytest.raises(ValidationError):
        quota2.save()


@pytest.mark.django_db
def test_update_active_successfully():
    # Create first active quota
    quota1 = EvaluationQuota(daily_limit=10, is_active=True)
    quota1.save()

    # Update the active quota
    quota1.daily_limit = 20
    quota1.save()


@pytest.mark.django_db
def test_update_to_active_when_another_active_exists():
    # Create first active quota
    quota1 = EvaluationQuota(daily_limit=10, is_active=True)
    quota1.save()

    # Create second inactive quota
    quota2 = EvaluationQuota(daily_limit=20, is_active=False)
    quota2.save()

    # Try to make second quota active
    quota2.is_active = True
    with pytest.raises(ValidationError):
        quota2.save()


@pytest.mark.django_db
def test_multiple_inactive_quotas_allowed():
    # Create first inactive quota
    quota1 = EvaluationQuota(daily_limit=10, is_active=False)
    quota1.save()

    # Create second inactive quota
    quota2 = EvaluationQuota(daily_limit=20, is_active=False)
    quota2.save()

    number_of_inactive_quotas = 2
    # Both should save successfully
    assert EvaluationQuota.objects.count() == number_of_inactive_quotas


@pytest.mark.django_db
def test_get_active_manager_method():
    # Create active quota
    active_quota = EvaluationQuota(daily_limit=10, is_active=True)
    active_quota.save()

    # Create inactive quota
    inactive_quota = EvaluationQuota(daily_limit=20, is_active=False)
    inactive_quota.save()

    # get_active() should return the active quota
    assert EvaluationQuota.objects.get_active() == active_quota

    # Deactivate the active quota
    active_quota.is_active = False
    active_quota.save()

    # Now get_active() should return None
    assert EvaluationQuota.objects.get_active() is None
