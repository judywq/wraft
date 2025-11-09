import pytest

from backend.myapp.admin import EvaluationLimitAdminForm
from backend.myapp.models import EvaluationLimit

pytestmark = pytest.mark.django_db


def make_form(data, instance=None):
    return EvaluationLimitAdminForm(data=data, instance=instance)


def test_create_active_limit_when_none_exists():
    form = make_form({"daily_limit": 10, "is_active": True})
    assert form.is_valid()
    limit = form.save()
    assert limit.is_active is True


def test_create_active_limit_when_one_exists():
    EvaluationLimit.objects.create(daily_limit=10, is_active=True)
    form = make_form({"daily_limit": 20, "is_active": True})
    assert not form.is_valid()
    assert "is_active" in form.errors
    assert "There can only be one active limit" in form.errors["is_active"][0]


def test_create_inactive_limit():
    EvaluationLimit.objects.create(daily_limit=10, is_active=True)
    form = make_form({"daily_limit": 20, "is_active": False})
    assert form.is_valid()
    limit = form.save()
    assert limit.is_active is False


def test_update_limit_to_active_when_another_active_exists():
    EvaluationLimit.objects.create(daily_limit=10, is_active=True)
    limit2 = EvaluationLimit.objects.create(daily_limit=20, is_active=False)
    form = make_form({"daily_limit": 20, "is_active": True}, instance=limit2)
    assert not form.is_valid()
    assert "is_active" in form.errors
    assert "There can only be one active limit" in form.errors["is_active"][0]


def test_update_limit_to_active_when_no_other_active_exists():
    limit = EvaluationLimit.objects.create(daily_limit=10, is_active=False)
    form = make_form({"daily_limit": 10, "is_active": True}, instance=limit)
    assert form.is_valid()
    updated_limit = form.save()
    assert updated_limit.is_active is True


def test_multiple_inactive_limits():
    form1 = make_form({"daily_limit": 10, "is_active": False})
    form2 = make_form({"daily_limit": 20, "is_active": False})
    assert form1.is_valid()
    assert form2.is_valid()
    limit1 = form1.save()
    limit2 = form2.save()
    assert not limit1.is_active
    assert not limit2.is_active
