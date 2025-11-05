import pytest

from backend.llm_caller.models import APIRequest
from backend.llm_caller.models import LLMConfig
from backend.llm_caller.models import LLMModel
from backend.llm_caller.models import QuotaConfig
from backend.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestLLMModel:
    def test_str_representation(self):
        model = LLMModel.objects.create(
            name="gpt-4",
            display_name="GPT-4",
            is_active=True,
        )
        assert str(model) == "GPT-4 (Active)"

    def test_save_default_model(self):
        # Create first model as default
        model1 = LLMModel.objects.create(
            name="gpt-4",
            display_name="GPT-4",
            is_default=True,
        )

        # Create second model as default
        model2 = LLMModel.objects.create(
            name="gpt-3.5",
            display_name="GPT-3.5",
            is_default=True,
        )

        # Refresh from database
        model1.refresh_from_db()
        model2.refresh_from_db()

        # Check that only model2 is default
        assert not model1.is_default
        assert model2.is_default

    def test_get_active_model(self):
        # Create inactive model
        LLMModel.objects.create(
            name="gpt-4",
            display_name="GPT-4",
            is_active=False,
        )

        # Create active model
        active_model = LLMModel.objects.create(
            name="gpt-3.5",
            display_name="GPT-3.5",
            is_active=True,
        )

        assert LLMModel.get_active_models().count() == 1
        assert LLMModel.get_active_models()[0] == active_model


class TestLLMConfig:
    def test_validate_user_prompt_template(self):
        new_model = LLMModel.objects.create(
            name="gpt-4",
            display_name="GPT-4",
            is_active=True,
        )

        # Valid template
        config = LLMConfig(
            model=new_model,
            purpose="surface_correction",
            user_prompt_template="Please evaluate this essay: {essay}",
        )
        config.full_clean()  # Should not raise


class TestQuotaConfig:
    def test_str_representation(self):
        model = LLMModel.objects.create(
            name="gpt-4",
            display_name="GPT-4",
        )
        quota = QuotaConfig.objects.create(
            model=model,
            daily_limit=100,
        )
        assert str(quota) == "QuotaConfig(GPT-4, limit=100)"


class TestAPIRequest:
    def test_str_representation(self):
        user = UserFactory()
        model = LLMModel.objects.create(
            name="gpt-4",
            display_name="GPT-4",
        )
        request = APIRequest.objects.create(
            created_by=user,
            model=model,
            input_json={"essay": "This is a test essay"},
            user_prompt_template="Please evaluate this essay: {essay}",
        )
        assert "APIRequest" in str(request)
        assert str(user) in str(request)
        assert str(model.display_name) in str(request)
