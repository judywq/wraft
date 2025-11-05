import pytest

from backend.myapp.admin import EvaluationQuotaAdminForm
from backend.myapp.models import EvaluationQuota

pytestmark = pytest.mark.django_db


def make_form(data, instance=None):
    return EvaluationQuotaAdminForm(data=data, instance=instance)


def test_create_active_quota_when_none_exists():
    form = make_form({"daily_limit": 10, "is_active": True})
    assert form.is_valid()
    quota = form.save()
    assert quota.is_active is True


def test_create_active_quota_when_one_exists():
    EvaluationQuota.objects.create(daily_limit=10, is_active=True)
    form = make_form({"daily_limit": 20, "is_active": True})
    assert not form.is_valid()
    assert "is_active" in form.errors
    assert "There can only be one active quota" in form.errors["is_active"][0]


def test_create_inactive_quota():
    EvaluationQuota.objects.create(daily_limit=10, is_active=True)
    form = make_form({"daily_limit": 20, "is_active": False})
    assert form.is_valid()
    quota = form.save()
    assert quota.is_active is False


def test_update_quota_to_active_when_another_active_exists():
    EvaluationQuota.objects.create(daily_limit=10, is_active=True)
    quota2 = EvaluationQuota.objects.create(daily_limit=20, is_active=False)
    form = make_form({"daily_limit": 20, "is_active": True}, instance=quota2)
    assert not form.is_valid()
    assert "is_active" in form.errors
    assert "There can only be one active quota" in form.errors["is_active"][0]


def test_update_quota_to_active_when_no_other_active_exists():
    quota = EvaluationQuota.objects.create(daily_limit=10, is_active=False)
    form = make_form({"daily_limit": 10, "is_active": True}, instance=quota)
    assert form.is_valid()
    updated_quota = form.save()
    assert updated_quota.is_active is True


def test_multiple_inactive_quotas():
    form1 = make_form({"daily_limit": 10, "is_active": False})
    form2 = make_form({"daily_limit": 20, "is_active": False})
    assert form1.is_valid()
    assert form2.is_valid()
    quota1 = form1.save()
    quota2 = form2.save()
    assert not quota1.is_active
    assert not quota2.is_active
