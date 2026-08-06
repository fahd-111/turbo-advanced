"""Tenancy isolation and the connect/callback endpoints."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse

from growth.models import ConnectionStatus, Platform
from growth.tests.conftest import callback_token

pytestmark = pytest.mark.django_db


def test_anonymous_users_get_nothing(api_client):
    assert api_client.get(reverse("growth:business-list")).status_code == 401


def test_list_only_returns_your_own_businesses(
    api_client, owner, business, other_business
):
    api_client.force_authenticate(owner)

    response = api_client.get(reverse("growth:business-list"))

    assert response.status_code == 200
    names = [row["name"] for row in response.data["results"]]
    assert names == [business.name]


def test_cannot_read_another_owners_business(api_client, owner, other_business):
    api_client.force_authenticate(owner)

    url = reverse("growth:business-detail", args=[other_business.pk])

    assert api_client.get(url).status_code == 404


def test_cannot_delete_another_owners_business(api_client, owner, other_business):
    api_client.force_authenticate(owner)

    url = reverse("growth:business-detail", args=[other_business.pk])
    assert api_client.delete(url).status_code == 404
    assert type(other_business).objects.filter(pk=other_business.pk).exists()


def test_create_assigns_the_requesting_user_as_owner(api_client, owner, other_user):
    api_client.force_authenticate(owner)

    response = api_client.post(
        reverse("growth:business-list"),
        {"name": "New Shop", "timezone": "Europe/Berlin", "owner": other_user.pk},
        format="json",
    )

    assert response.status_code == 201
    from growth.models import Business

    assert Business.objects.get(name="New Shop").owner == owner


def test_create_rejects_an_invalid_timezone(api_client, owner):
    api_client.force_authenticate(owner)

    response = api_client.post(
        reverse("growth:business-list"),
        {"name": "Bad TZ", "timezone": "Mars/Olympus"},
        format="json",
    )

    assert response.status_code == 400
    assert "timezone" in response.data


def test_connect_returns_the_consent_url(api_client, owner, business):
    api_client.force_authenticate(owner)
    client = MagicMock()
    client.connected_accounts.link.return_value = SimpleNamespace(
        id="ca_1", status="INITIATED", redirect_url="https://composio/oauth"
    )

    with (
        patch("growth.services.connections.get_client", return_value=client),
        patch("growth.services.connections.auth_config_id", return_value="ac_ig"),
    ):
        response = api_client.post(
            reverse("growth:business-connect", args=[business.pk]),
            {"platform": Platform.INSTAGRAM},
            format="json",
        )

    assert response.status_code == 200
    assert response.data["redirect_url"] == "https://composio/oauth"
    assert response.data["connection"]["status"] == ConnectionStatus.PENDING


def test_connect_rejects_an_unknown_platform(api_client, owner, business):
    api_client.force_authenticate(owner)

    response = api_client.post(
        reverse("growth:business-connect", args=[business.pk]),
        {"platform": "tiktok"},
        format="json",
    )

    assert response.status_code == 400


def test_connect_without_composio_configured_returns_503(api_client, owner, business):
    api_client.force_authenticate(owner)

    with patch.object(
        __import__("django.conf", fromlist=["settings"]).settings,
        "COMPOSIO_API_KEY",
        "",
    ):
        response = api_client.post(
            reverse("growth:business-connect", args=[business.pk]),
            {"platform": Platform.INSTAGRAM},
            format="json",
        )

    assert response.status_code == 503


def test_composio_api_errors_become_502_not_500(api_client, owner, business):
    """An under-privileged key or a Composio outage must not surface as a 500."""
    import httpx
    from composio_client import PermissionDeniedError

    error = PermissionDeniedError(
        "insufficient permissions",
        response=httpx.Response(
            403, request=httpx.Request("POST", "https://backend.composio.dev")
        ),
        body=None,
    )
    client = MagicMock()
    client.connected_accounts.link.side_effect = error

    api_client.force_authenticate(owner)
    with (
        patch("growth.services.connections.get_client", return_value=client),
        patch("growth.services.connections.auth_config_id", return_value="ac_ig"),
    ):
        response = api_client.post(
            reverse("growth:business-connect", args=[business.pk]),
            {"platform": Platform.INSTAGRAM},
            format="json",
        )

    assert response.status_code == 502
    assert "Composio rejected the request" in response.data["detail"]


def test_composio_sdk_errors_also_become_502(api_client, owner, business):
    """The SDK's own hierarchy (retired endpoints, missing toolkits) is separate
    from the HTTP client's and must be caught too."""
    from composio.exceptions import (
        ComposioLegacyConnectedAccountsEndpointRetiredError,
    )

    client = MagicMock()
    client.connected_accounts.link.side_effect = (
        ComposioLegacyConnectedAccountsEndpointRetiredError("endpoint retired")
    )

    api_client.force_authenticate(owner)
    with (
        patch("growth.services.connections.get_client", return_value=client),
        patch("growth.services.connections.auth_config_id", return_value="ac_ig"),
    ):
        response = api_client.post(
            reverse("growth:business-connect", args=[business.pk]),
            {"platform": Platform.INSTAGRAM},
            format="json",
        )

    assert response.status_code == 502


def test_cannot_connect_another_owners_business(api_client, owner, other_business):
    api_client.force_authenticate(owner)

    response = api_client.post(
        reverse("growth:business-connect", args=[other_business.pk]),
        {"platform": Platform.INSTAGRAM},
        format="json",
    )

    assert response.status_code == 404


def test_connections_list_is_scoped_to_the_owner(
    api_client, owner, other_business, instagram_connection
):
    other_business.connections.create(platform=Platform.FACEBOOK)
    api_client.force_authenticate(owner)

    response = api_client.get(reverse("growth:connection-list"))

    assert response.status_code == 200
    assert [row["id"] for row in response.data["results"]] == [instagram_connection.pk]


def test_health_check_endpoint_refreshes_status(
    api_client, owner, instagram_connection
):
    api_client.force_authenticate(owner)
    client = MagicMock()
    client.connected_accounts.get.return_value = SimpleNamespace(
        status="EXPIRED", status_reason="token revoked"
    )

    with patch("growth.services.connections.get_client", return_value=client):
        response = api_client.post(
            reverse("growth:connection-check-health", args=[instagram_connection.pk])
        )

    assert response.status_code == 200
    assert response.data["status"] == ConnectionStatus.NEEDS_REAUTH


def test_callback_syncs_the_connection(api_client, instagram_connection):
    token = callback_token(instagram_connection)

    client = MagicMock()
    client.connected_accounts.get.return_value = SimpleNamespace(
        status="ACTIVE", status_reason=""
    )

    with patch("growth.services.connections.get_client", return_value=client):
        response = api_client.get(
            reverse("growth:connection-callback"), {"token": token}
        )

    assert response.status_code == 200
    assert response.json()["status"] == ConnectionStatus.HEALTHY


def test_callback_rejects_a_forged_token(api_client):
    response = api_client.get(
        reverse("growth:connection-callback"), {"token": "1:nope"}
    )

    assert response.status_code == 400
