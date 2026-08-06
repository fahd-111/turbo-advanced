import pytest
from django.core.exceptions import ValidationError

from growth.models import (
    AuditLog,
    ConnectionStatus,
    SocialConnection,
    validate_timezone,
)

pytestmark = pytest.mark.django_db


def test_composio_user_id_is_scoped_to_the_business(business):
    assert business.composio_user_id == f"business_{business.pk}"


@pytest.mark.parametrize("value", ["UTC", "Europe/Berlin", "America/New_York"])
def test_validate_timezone_accepts_iana_zones(value):
    validate_timezone(value)


@pytest.mark.parametrize("value", ["", "Mars/Olympus", "GMT+2", "europe/berlin"])
def test_validate_timezone_rejects_everything_else(value):
    with pytest.raises(ValidationError):
        validate_timezone(value)


def test_is_usable_requires_healthy_status_and_both_ids(instagram_connection):
    assert instagram_connection.is_usable is True

    instagram_connection.status = ConnectionStatus.NEEDS_REAUTH
    assert instagram_connection.is_usable is False

    instagram_connection.status = ConnectionStatus.HEALTHY
    instagram_connection.external_account_id = ""
    assert instagram_connection.is_usable is False


def test_one_connection_per_platform_per_business(business, instagram_connection):
    from django.db import IntegrityError

    with pytest.raises(IntegrityError):
        SocialConnection.objects.create(
            business=business, platform=instagram_connection.platform
        )


def test_audit_log_record_stores_kwargs_as_payload(business):
    entry = AuditLog.record(business, "post.published", external_post_id="123")

    assert entry.actor == AuditLog.Actor.AGENT
    assert entry.payload == {"external_post_id": "123"}
    assert business.audit_logs.count() == 1
