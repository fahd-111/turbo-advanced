"""Connecting a business's Instagram/Facebook account through Composio."""

import logging
from typing import Any
from urllib.parse import urlencode

from django.conf import settings
from django.core import signing
from django.urls import reverse
from django.utils import timezone

from growth.models import (
    AuditLog,
    Business,
    ConnectionStatus,
    Platform,
    SocialConnection,
)
from growth.services import tools
from growth.services.composio_client import (
    COMPOSIO_FAILURES,
    ToolExecutionError,
    auth_config_id,
    execute_tool,
    get_client,
)

logger = logging.getLogger(__name__)

# Composio's connected-account states mapped onto ours.
COMPOSIO_STATUS_MAP = {
    "INITIALIZING": ConnectionStatus.PENDING,
    "INITIATED": ConnectionStatus.PENDING,
    "ACTIVE": ConnectionStatus.HEALTHY,
    "EXPIRED": ConnectionStatus.NEEDS_REAUTH,
    "FAILED": ConnectionStatus.NEEDS_REAUTH,
    "INACTIVE": ConnectionStatus.DISCONNECTED,
    "REVOKED": ConnectionStatus.DISCONNECTED,
}


# The OAuth callback is necessarily unauthenticated, so the connection it refers
# to travels as a signed token rather than a guessable primary key.
CALLBACK_SALT = "growth.connection.callback"
CALLBACK_MAX_AGE = 60 * 60  # an OAuth consent screen the user leaves open


def callback_url(connection: SocialConnection) -> str:
    token = signing.dumps(connection.pk, salt=CALLBACK_SALT)
    path = reverse("growth:connection-callback")
    return f"{settings.PUBLIC_API_URL.rstrip('/')}{path}?{urlencode({'token': token})}"


def connection_from_token(token: str) -> SocialConnection:
    """Resolve a callback token. Raises BadSignature if forged or expired."""
    pk = signing.loads(token, salt=CALLBACK_SALT, max_age=CALLBACK_MAX_AGE)
    return SocialConnection.objects.select_related("business").get(pk=pk)


def initiate_connection(
    business: Business, platform: str
) -> tuple[SocialConnection, str]:
    """Start the OAuth flow. Returns the connection row and the consent URL."""
    connection, _created = SocialConnection.objects.get_or_create(
        business=business, platform=platform
    )

    # link(), not initiate(): the latter is retired for Composio-managed OAuth
    # auth configs and now 400s. Same signature, same ConnectionRequest back.
    request = get_client().connected_accounts.link(
        user_id=business.composio_user_id,
        auth_config_id=auth_config_id(platform),
        callback_url=callback_url(connection),
    )

    connection.composio_connected_account_id = request.id
    connection.status = ConnectionStatus.PENDING
    connection.last_error = ""
    connection.save(
        update_fields=[
            "composio_connected_account_id",
            "status",
            "last_error",
            "modified_at",
        ]
    )

    AuditLog.record(
        business,
        "connection.initiated",
        actor=AuditLog.Actor.USER,
        platform=platform,
        connected_account_id=request.id,
    )

    if not request.redirect_url:
        raise RuntimeError(
            f"Composio returned no redirect URL for {platform}; "
            "check that the auth config uses OAuth2."
        )
    return connection, request.redirect_url


def sync_connection(connection: SocialConnection) -> SocialConnection:
    """Refresh status from Composio and fill in the external account id."""
    if not connection.composio_connected_account_id:
        connection.status = ConnectionStatus.DISCONNECTED
        connection.last_checked_at = timezone.now()
        connection.save(update_fields=["status", "last_checked_at", "modified_at"])
        return connection

    account = get_client().connected_accounts.get(
        connection.composio_connected_account_id
    )
    previous = connection.status
    connection.status = COMPOSIO_STATUS_MAP.get(
        account.status, ConnectionStatus.DISCONNECTED
    )
    connection.last_checked_at = timezone.now()
    connection.last_error = getattr(account, "status_reason", "") or ""

    if (
        connection.status == ConnectionStatus.HEALTHY
        and not connection.external_account_id
    ):
        _resolve_external_account(connection)

    connection.save()

    if previous != connection.status:
        AuditLog.record(
            connection.business,
            "connection.status_changed",
            actor=AuditLog.Actor.SYSTEM,
            platform=connection.platform,
            previous=previous,
            current=connection.status,
        )
    return connection


def _resolve_external_account(connection: SocialConnection) -> None:
    """Best effort lookup of the Instagram user id / Facebook Page id.

    A failure here leaves the ids blank rather than failing the whole sync: the
    connection is genuinely authorised, we just cannot publish through it yet,
    which ``SocialConnection.is_usable`` already reports.
    """
    try:
        if connection.platform == Platform.FACEBOOK:
            data = execute_tool(
                tools.FB_LIST_MANAGED_PAGES,
                {},
                connected_account_id=connection.composio_connected_account_id,
                user_id=connection.business.composio_user_id,
            )
            page = _first_record(data)
            if page:
                connection.external_account_id = str(page.get("id", ""))
                connection.external_account_name = str(page.get("name", ""))
        else:
            data = execute_tool(
                tools.IG_GET_USER_INFO,
                {"ig_user_id": tools.SELF},
                connected_account_id=connection.composio_connected_account_id,
                user_id=connection.business.composio_user_id,
            )
            connection.external_account_id = str(data.get("id") or "")
            connection.external_account_name = str(
                data.get("username") or data.get("name") or ""
            )
    except (ToolExecutionError, RuntimeError, *COMPOSIO_FAILURES) as exc:
        # Must swallow every Composio-origin failure: an escape here skips the
        # caller's save() and silently discards the status we just fetched.
        logger.warning(
            "growth.connection.account_lookup_failed",
            extra={"connection_id": connection.pk, "error": str(exc)},
        )
        connection.last_error = f"Could not resolve account id: {exc}"


def _first_record(data: dict[str, Any]) -> dict[str, Any] | None:
    """Pull the first item out of a Composio list-shaped response."""
    for key in ("data", "items", "pages", "results"):
        value = data.get(key)
        if isinstance(value, list) and value:
            return value[0] if isinstance(value[0], dict) else None
        if isinstance(value, dict):
            return _first_record(value) or value
    return None


def disconnect(connection: SocialConnection) -> None:
    """Revoke at Composio and mark the row disconnected."""
    if connection.composio_connected_account_id:
        try:
            get_client().connected_accounts.delete(
                connection.composio_connected_account_id
            )
        except Exception as exc:  # noqa: BLE001 - deletion is best effort
            logger.warning(
                "growth.connection.delete_failed",
                extra={"connection_id": connection.pk, "error": str(exc)},
            )

    connection.status = ConnectionStatus.DISCONNECTED
    connection.composio_connected_account_id = ""
    connection.external_account_id = ""
    connection.save()

    AuditLog.record(
        connection.business,
        "connection.disconnected",
        actor=AuditLog.Actor.USER,
        platform=connection.platform,
    )
