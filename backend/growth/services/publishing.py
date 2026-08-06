"""Publishing a single image post to Instagram or Facebook via Composio."""

import logging
from dataclasses import dataclass, field
from typing import Any

from growth.models import AuditLog, ConnectionStatus, Platform, SocialConnection
from growth.services import tools
from growth.services.composio_client import ToolExecutionError, execute_tool

logger = logging.getLogger(__name__)

# Leave headroom under Meta's rolling 24h publish cap so a burst never gets us
# rate limited mid-queue.
QUOTA_HEADROOM = 2


class PublishingPaused(RuntimeError):
    """The business kill switch is on, or the connection is not usable."""


class QuotaExhausted(RuntimeError):
    """The account is at Meta's rolling 24h publishing cap."""


@dataclass
class PublishResult:
    external_post_id: str
    raw: dict[str, Any] = field(default_factory=dict)


def publish_image_post(
    connection: SocialConnection, *, caption: str, image_url: str
) -> PublishResult:
    """Publish one image + caption. Raises on any refusal or failure."""
    # Re-read the kill switch here rather than trusting the caller's copy: this
    # is the last point before we touch a live account.
    connection.refresh_from_db()
    business = connection.business

    if business.publishing_paused:
        raise PublishingPaused(f"Publishing is paused for {business.name}")
    if connection.status != ConnectionStatus.HEALTHY:
        raise PublishingPaused(
            f"{connection} is {connection.get_status_display()}, not healthy"
        )
    if not connection.is_usable:
        raise PublishingPaused(f"{connection} is missing its external account id")

    if connection.platform == Platform.INSTAGRAM:
        result = _publish_instagram(connection, caption=caption, image_url=image_url)
    else:
        result = _publish_facebook(connection, caption=caption, image_url=image_url)

    AuditLog.record(
        business,
        "post.published",
        platform=connection.platform,
        external_post_id=result.external_post_id,
        image_url=image_url,
    )
    return result


def _publish_instagram(
    connection: SocialConnection, *, caption: str, image_url: str
) -> PublishResult:
    """Two step flow: create a media container, then publish it."""
    ensure_instagram_quota(connection)

    container = execute_tool(
        tools.IG_CREATE_MEDIA_CONTAINER,
        {
            "ig_user_id": connection.external_account_id,
            "image_url": image_url,
            "caption": caption,
        },
        connected_account_id=connection.composio_connected_account_id,
        user_id=connection.business.composio_user_id,
    )
    container_id = _extract_id(container)
    if not container_id:
        raise ToolExecutionError(
            tools.IG_CREATE_MEDIA_CONTAINER,
            "response contained no container id",
            container,
        )

    published = execute_tool(
        tools.IG_PUBLISH_MEDIA,
        {
            "ig_user_id": connection.external_account_id,
            "creation_id": container_id,
        },
        connected_account_id=connection.composio_connected_account_id,
        user_id=connection.business.composio_user_id,
    )
    return PublishResult(_extract_id(published) or container_id, published)


def _publish_facebook(
    connection: SocialConnection, *, caption: str, image_url: str
) -> PublishResult:
    data = execute_tool(
        tools.FB_CREATE_PHOTO_POST,
        {
            "page_id": connection.external_account_id,
            "url": image_url,
            # "message" is the schema's property name; "caption" is undeclared.
            "message": caption,
        },
        connected_account_id=connection.composio_connected_account_id,
        user_id=connection.business.composio_user_id,
    )
    post_id = data.get("post_id") or _extract_id(data)
    if not post_id:
        raise ToolExecutionError(
            tools.FB_CREATE_PHOTO_POST, "response contained no post id", data
        )
    return PublishResult(str(post_id), data)


def ensure_instagram_quota(connection: SocialConnection) -> None:
    """Raise QuotaExhausted if the account is at Meta's 24h publish cap.

    A quota response we cannot parse is treated as "unknown, go ahead": failing
    closed here would stall every queue on a response-shape change, and a real
    cap breach still surfaces as an ordinary publish failure.
    """
    try:
        data = execute_tool(
            tools.IG_PUBLISHING_LIMIT,
            {"ig_user_id": connection.external_account_id},
            connected_account_id=connection.composio_connected_account_id,
            user_id=connection.business.composio_user_id,
        )
    except ToolExecutionError as exc:
        logger.warning(
            "growth.publish.quota_check_failed",
            extra={"connection_id": connection.pk, "error": str(exc)},
        )
        return

    used, total = _parse_quota(data)
    if used is None or total is None:
        logger.info(
            "growth.publish.quota_unparsed", extra={"connection_id": connection.pk}
        )
        return

    if used >= total - QUOTA_HEADROOM:
        raise QuotaExhausted(
            f"Instagram publishing quota nearly exhausted ({used}/{total})"
        )


def _parse_quota(data: dict[str, Any]) -> tuple[int | None, int | None]:
    record: Any = data
    if isinstance(data.get("data"), list) and data["data"]:
        record = data["data"][0]
    if not isinstance(record, dict):
        return None, None

    used = record.get("quota_usage")
    config = record.get("config")
    total = config.get("quota_total") if isinstance(config, dict) else None
    if isinstance(used, int) and isinstance(total, int):
        return used, total
    return None, None


def _extract_id(data: dict[str, Any]) -> str:
    for key in ("id", "creation_id", "media_id"):
        value = data.get(key)
        if value:
            return str(value)
    nested = data.get("data")
    if isinstance(nested, dict):
        return _extract_id(nested)
    return ""
