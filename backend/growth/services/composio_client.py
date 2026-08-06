"""Thin wrapper around the Composio SDK.

Every Composio call in this codebase goes through here so that timeouts, HTTP
retries, and structured logging are configured in exactly one place. The SDK
handles transport-level retry itself (``max_retries``); this module adds the
"tool ran but reported failure" case, which the SDK returns rather than raises.
"""

import logging
from functools import lru_cache
from typing import Any

from composio import Composio
from composio.exceptions import ComposioError as ComposioSDKError
from composio_client import APIError as ComposioAPIError
from django.conf import settings

logger = logging.getLogger(__name__)

# The SDK raises from two unrelated hierarchies: transport errors from
# composio_client, and semantic ones (retired endpoints, missing toolkits) from
# composio.exceptions. Catch both, or the second kind surfaces as a 500.
COMPOSIO_FAILURES = (ComposioAPIError, ComposioSDKError)

__all__ = [
    "COMPOSIO_FAILURES",
    "ComposioAPIError",
    "ComposioNotConfigured",
    "ComposioSDKError",
    "ToolExecutionError",
    "auth_config_id",
    "execute_tool",
    "get_client",
]


class ComposioNotConfigured(RuntimeError):
    """COMPOSIO_API_KEY (or an auth config id) is missing from the environment."""


class ToolExecutionError(RuntimeError):
    """A Composio tool executed but reported failure."""

    def __init__(self, slug: str, error: str, data: dict[str, Any] | None = None):
        super().__init__(f"{slug} failed: {error}")
        self.slug = slug
        self.error = error
        self.data = data or {}


@lru_cache(maxsize=1)
def get_client() -> Composio:
    if not settings.COMPOSIO_API_KEY:
        raise ComposioNotConfigured("COMPOSIO_API_KEY is not set")
    return Composio(
        api_key=settings.COMPOSIO_API_KEY,
        timeout=settings.COMPOSIO_TIMEOUT_SECONDS,
        max_retries=settings.COMPOSIO_MAX_RETRIES,
        toolkit_versions=settings.COMPOSIO_TOOLKIT_VERSIONS,
    )


def auth_config_id(platform: str) -> str:
    config_id = settings.COMPOSIO_AUTH_CONFIG_IDS.get(platform, "")
    if not config_id:
        raise ComposioNotConfigured(
            f"No Composio auth config id configured for platform '{platform}'"
        )
    return config_id


def execute_tool(
    slug: str,
    arguments: dict[str, Any],
    *,
    connected_account_id: str,
    user_id: str,
) -> dict[str, Any]:
    """Execute a Composio tool and return its ``data`` payload.

    Raises ToolExecutionError when the tool reports ``successful=False``.
    """
    logger.info(
        "composio.tool.execute",
        extra={"slug": slug, "user_id": user_id, "arguments": sorted(arguments)},
    )
    response = get_client().tools.execute(
        slug,
        arguments,
        user_id=user_id,
        connected_account_id=connected_account_id,
    )
    # ToolExecutionResponse is a TypedDict, not an object: subscript, never dot.
    if not response["successful"]:
        error = response.get("error") or "unknown error"
        logger.warning(
            "composio.tool.failed",
            extra={"slug": slug, "user_id": user_id, "error": error},
        )
        raise ToolExecutionError(slug, error, response.get("data"))

    logger.info("composio.tool.ok", extra={"slug": slug, "user_id": user_id})
    return response.get("data") or {}
