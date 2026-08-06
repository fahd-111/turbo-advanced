from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.core.signing import BadSignature

from growth.models import AuditLog, ConnectionStatus, Platform
from growth.services import connections as connection_service
from growth.services.composio_client import ComposioSDKError, ToolExecutionError
from growth.tests.conftest import callback_token

pytestmark = pytest.mark.django_db


def composio_account(status: str, reason: str = ""):
    return SimpleNamespace(status=status, status_reason=reason)


@pytest.mark.parametrize(
    ("composio_status", "expected"),
    [
        ("ACTIVE", ConnectionStatus.HEALTHY),
        ("INITIATED", ConnectionStatus.PENDING),
        ("INITIALIZING", ConnectionStatus.PENDING),
        ("EXPIRED", ConnectionStatus.NEEDS_REAUTH),
        ("FAILED", ConnectionStatus.NEEDS_REAUTH),
        ("INACTIVE", ConnectionStatus.DISCONNECTED),
        ("REVOKED", ConnectionStatus.DISCONNECTED),
        ("SOMETHING_NEW", ConnectionStatus.DISCONNECTED),
    ],
)
def test_sync_maps_composio_status(instagram_connection, composio_status, expected):
    client = MagicMock()
    client.connected_accounts.get.return_value = composio_account(composio_status)

    with patch("growth.services.connections.get_client", return_value=client):
        connection = connection_service.sync_connection(instagram_connection)

    assert connection.status == expected
    assert connection.last_checked_at is not None


def test_sync_records_an_audit_entry_only_when_status_changes(instagram_connection):
    client = MagicMock()
    client.connected_accounts.get.return_value = composio_account("ACTIVE")

    with patch("growth.services.connections.get_client", return_value=client):
        connection_service.sync_connection(instagram_connection)
        assert not AuditLog.objects.filter(action="connection.status_changed").exists()

        client.connected_accounts.get.return_value = composio_account("EXPIRED")
        connection_service.sync_connection(instagram_connection)

    assert AuditLog.objects.filter(action="connection.status_changed").count() == 1


def test_sync_without_a_composio_account_marks_disconnected(business):
    connection = business.connections.create(platform=Platform.FACEBOOK)

    connection = connection_service.sync_connection(connection)

    assert connection.status == ConnectionStatus.DISCONNECTED


@pytest.mark.parametrize(
    "failure",
    [
        RuntimeError("no such tool"),
        ToolExecutionError("FACEBOOK_LIST_MANAGED_PAGES", "boom"),
        ComposioSDKError("toolkit version not specified"),
    ],
    ids=["runtime", "tool-execution", "composio-sdk"],
)
def test_account_lookup_failure_leaves_the_connection_healthy(business, failure):
    """Composio says authorised; we just could not read the page id yet.

    The status we already fetched must survive: an exception escaping the lookup
    would skip sync_connection's save() and silently leave the row 'pending'.
    """
    connection = business.connections.create(
        platform=Platform.FACEBOOK, composio_connected_account_id="ca_fb_1"
    )
    client = MagicMock()
    client.connected_accounts.get.return_value = composio_account("ACTIVE")

    with (
        patch("growth.services.connections.get_client", return_value=client),
        patch("growth.services.connections.execute_tool", side_effect=failure),
    ):
        connection = connection_service.sync_connection(connection)

    connection.refresh_from_db()
    assert connection.status == ConnectionStatus.HEALTHY
    assert connection.external_account_id == ""
    assert connection.is_usable is False
    assert "Could not resolve account id" in connection.last_error


def test_instagram_account_id_is_read_via_the_me_alias(instagram_connection):
    """We cannot pass our own id before we know it, so the lookup uses "me"."""
    instagram_connection.external_account_id = ""
    instagram_connection.save()

    client = MagicMock()
    client.connected_accounts.get.return_value = composio_account("ACTIVE")
    info = {"id": "27697800669843148", "username": "acme._.coffee", "name": "Acme"}

    with (
        patch("growth.services.connections.get_client", return_value=client),
        patch("growth.services.connections.execute_tool", return_value=info) as execute,
    ):
        connection = connection_service.sync_connection(instagram_connection)

    assert execute.call_args.args[1] == {"ig_user_id": "me"}
    assert connection.external_account_id == "27697800669843148"
    assert connection.external_account_name == "acme._.coffee"
    assert connection.is_usable is True


def test_facebook_page_id_is_read_from_the_managed_pages_response(business):
    connection = business.connections.create(
        platform=Platform.FACEBOOK, composio_connected_account_id="ca_fb_1"
    )
    client = MagicMock()
    client.connected_accounts.get.return_value = composio_account("ACTIVE")
    pages = {"data": [{"id": "5150", "name": "Acme Coffee Page"}]}

    with (
        patch("growth.services.connections.get_client", return_value=client),
        patch("growth.services.connections.execute_tool", return_value=pages),
    ):
        connection = connection_service.sync_connection(connection)

    assert connection.external_account_id == "5150"
    assert connection.external_account_name == "Acme Coffee Page"
    assert connection.is_usable is True


def test_callback_token_round_trips(instagram_connection):
    token = callback_token(instagram_connection)

    assert connection_service.connection_from_token(token) == instagram_connection


def test_forged_callback_token_is_rejected():
    with pytest.raises(BadSignature):
        connection_service.connection_from_token("1:forged-signature")


def test_initiate_stores_the_connected_account_id(business):
    client = MagicMock()
    client.connected_accounts.link.return_value = SimpleNamespace(
        id="ca_new_1", status="INITIATED", redirect_url="https://composio/oauth"
    )

    with (
        patch("growth.services.connections.get_client", return_value=client),
        patch("growth.services.connections.auth_config_id", return_value="ac_ig"),
    ):
        connection, redirect_url = connection_service.initiate_connection(
            business, Platform.INSTAGRAM
        )

    assert redirect_url == "https://composio/oauth"
    assert connection.composio_connected_account_id == "ca_new_1"
    assert connection.status == ConnectionStatus.PENDING
    assert AuditLog.objects.filter(action="connection.initiated").exists()

    # Composio must be told which tenant this belongs to.
    kwargs = client.connected_accounts.link.call_args.kwargs
    assert kwargs["user_id"] == business.composio_user_id


def test_initiate_is_idempotent_per_platform(business):
    client = MagicMock()
    client.connected_accounts.link.return_value = SimpleNamespace(
        id="ca_new_2", status="INITIATED", redirect_url="https://composio/oauth"
    )

    with (
        patch("growth.services.connections.get_client", return_value=client),
        patch("growth.services.connections.auth_config_id", return_value="ac_ig"),
    ):
        connection_service.initiate_connection(business, Platform.INSTAGRAM)
        connection_service.initiate_connection(business, Platform.INSTAGRAM)

    assert business.connections.filter(platform=Platform.INSTAGRAM).count() == 1


def test_disconnect_clears_ids_even_if_composio_errors(instagram_connection):
    client = MagicMock()
    client.connected_accounts.delete.side_effect = RuntimeError("gone")

    with patch("growth.services.connections.get_client", return_value=client):
        connection_service.disconnect(instagram_connection)

    instagram_connection.refresh_from_db()
    assert instagram_connection.status == ConnectionStatus.DISCONNECTED
    assert instagram_connection.composio_connected_account_id == ""
    assert instagram_connection.external_account_id == ""
