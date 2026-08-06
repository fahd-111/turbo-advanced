"""Covers the seam between our code and the Composio SDK's response shape.

``ToolExecutionResponse`` is a TypedDict, so these tests deliberately feed
execute_tool plain dicts rather than mocks with attributes: an attribute-style
read would pass against a MagicMock and fail against the real SDK.
"""

from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings

from growth.services.composio_client import (
    ComposioNotConfigured,
    ToolExecutionError,
    auth_config_id,
    execute_tool,
    get_client,
)


def run_tool(response: dict):
    client = MagicMock()
    client.tools.execute.return_value = response
    with patch("growth.services.composio_client.get_client", return_value=client):
        return execute_tool(
            "SOME_TOOL", {"a": 1}, connected_account_id="ca_1", user_id="business_1"
        )


def test_successful_execution_returns_the_data_payload():
    assert run_tool({"successful": True, "error": None, "data": {"id": "7"}}) == {
        "id": "7"
    }


def test_successful_execution_with_no_data_returns_an_empty_dict():
    assert run_tool({"successful": True, "error": None, "data": None}) == {}


def test_failed_execution_raises_with_the_reported_error():
    with pytest.raises(ToolExecutionError) as exc_info:
        run_tool({"successful": False, "error": "bad token", "data": {"code": 190}})

    assert exc_info.value.error == "bad token"
    assert exc_info.value.data == {"code": 190}
    assert exc_info.value.slug == "SOME_TOOL"


def test_failure_without_an_error_message_still_raises():
    with pytest.raises(ToolExecutionError) as exc_info:
        run_tool({"successful": False, "error": None, "data": {}})

    assert exc_info.value.error == "unknown error"


def test_arguments_and_identity_are_forwarded_to_the_sdk():
    client = MagicMock()
    client.tools.execute.return_value = {"successful": True, "error": None, "data": {}}

    with patch("growth.services.composio_client.get_client", return_value=client):
        execute_tool(
            "SOME_TOOL", {"a": 1}, connected_account_id="ca_9", user_id="business_3"
        )

    args, kwargs = client.tools.execute.call_args
    assert args == ("SOME_TOOL", {"a": 1})
    assert kwargs["user_id"] == "business_3"
    assert kwargs["connected_account_id"] == "ca_9"


@override_settings(COMPOSIO_API_KEY="")
def test_missing_api_key_is_a_clear_error():
    get_client.cache_clear()
    try:
        with pytest.raises(ComposioNotConfigured):
            get_client()
    finally:
        get_client.cache_clear()


@override_settings(COMPOSIO_AUTH_CONFIG_IDS={"instagram": "", "facebook": "ac_fb"})
def test_missing_auth_config_names_the_platform():
    assert auth_config_id("facebook") == "ac_fb"

    with pytest.raises(ComposioNotConfigured, match="instagram"):
        auth_config_id("instagram")
