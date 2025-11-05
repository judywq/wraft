from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from backend.llm_caller.models import APIRequest
from backend.llm_caller.models import LLMModel
from backend.llm_caller.models import QuotaConfig
from backend.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    return api_client, user


@pytest.fixture
def active_model():
    model = LLMModel.objects.create(
        name="gpt-4",
        display_name="GPT-4",
        is_active=True,
        is_default=True,
    )
    QuotaConfig.objects.create(
        model=model,
        daily_limit=10,
    )
    return model


class TestActiveModelsView:
    def test_unauthenticated_access(self, api_client):
        url = reverse("active-models")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_active_models(self, authenticated_client, active_model):
        client, user = authenticated_client
        url = reverse("active-models")

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["display_name"] == active_model.display_name
        assert data[0]["used_quota"] == 0
        assert data[0]["daily_limit"] == 10  # noqa: PLR2004

    def test_quota_counting(self, authenticated_client, active_model):
        client, user = authenticated_client
        url = reverse("active-models")

        # Create some API requests
        APIRequest.objects.create(
            created_by=user,
            model=active_model,
            input_json={"essay": "Test essay"},
            user_prompt_template="Please evaluate this essay: {essay}",
            status=APIRequest.Status.COMPLETED,
        )

        # Create an old request that shouldn't count towards today's quota
        yesterday = timezone.now() - timedelta(days=1)
        req = APIRequest.objects.create(
            created_by=user,
            model=active_model,
            input_json={"essay": "Old essay"},
            user_prompt_template="Please evaluate this essay: {essay}",
            status=APIRequest.Status.COMPLETED,
        )
        req.created_at = yesterday
        req.save()

        response = client.get(url)
        data = response.json()
        assert data[0]["used_quota"] == 1  # Only today's request counts
