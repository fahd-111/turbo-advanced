from unittest.mock import patch

import pytest

from growth.models import AuditLog, ConnectionStatus
from growth.services import tools
from growth.services.composio_client import ToolExecutionError
from growth.services.publishing import (
    PublishingPaused,
    QuotaExhausted,
    ensure_instagram_quota,
    publish_image_post,
)

pytestmark = pytest.mark.django_db

QUOTA_OK = {"data": [{"quota_usage": 1, "config": {"quota_total": 50}}]}


def fake_tool_responses(**overrides):
    """Return a side effect that answers each tool slug with canned data."""
    responses = {
        tools.IG_PUBLISHING_LIMIT: QUOTA_OK,
        tools.IG_CREATE_MEDIA_CONTAINER: {"id": "container-1"},
        tools.IG_PUBLISH_MEDIA: {"id": "ig-media-9"},
        tools.FB_CREATE_PHOTO_POST: {"id": "photo-1", "post_id": "page_post-7"},
    }
    responses.update(overrides)

    def side_effect(slug, arguments, **kwargs):
        return responses[slug]

    return side_effect


def test_instagram_publishes_container_then_media(instagram_connection):
    with patch(
        "growth.services.publishing.execute_tool", side_effect=fake_tool_responses()
    ) as execute:
        result = publish_image_post(
            instagram_connection, caption="hello", image_url="https://img/1.jpg"
        )

    assert result.external_post_id == "ig-media-9"

    slugs = [call.args[0] for call in execute.call_args_list]
    assert slugs == [
        tools.IG_PUBLISHING_LIMIT,
        tools.IG_CREATE_MEDIA_CONTAINER,
        tools.IG_PUBLISH_MEDIA,
    ]

    # The publish step must carry the id produced by the container step.
    container_args = execute.call_args_list[1].args[1]
    publish_args = execute.call_args_list[2].args[1]
    assert container_args["image_url"] == "https://img/1.jpg"
    assert container_args["caption"] == "hello"
    assert publish_args["creation_id"] == "container-1"

    assert AuditLog.objects.filter(action="post.published").count() == 1


def test_facebook_prefers_the_page_scoped_post_id(facebook_connection):
    """Facebook returns both a photo id and a composite PageID_PostID; follow-up
    calls need the composite one."""
    with patch(
        "growth.services.publishing.execute_tool", side_effect=fake_tool_responses()
    ) as execute:
        result = publish_image_post(
            facebook_connection, caption="hi", image_url="https://img/2.jpg"
        )

    assert result.external_post_id == "page_post-7"

    # Verified against the live tool schema: the caption property is "message",
    # and "caption" is not declared at all.
    args = execute.call_args.args[1]
    assert args == {
        "page_id": facebook_connection.external_account_id,
        "url": "https://img/2.jpg",
        "message": "hi",
    }


def test_instagram_sends_exactly_the_documented_arguments(instagram_connection):
    with patch(
        "growth.services.publishing.execute_tool", side_effect=fake_tool_responses()
    ) as execute:
        publish_image_post(
            instagram_connection, caption="hello", image_url="https://img/1.jpg"
        )

    assert execute.call_args_list[1].args[1] == {
        "ig_user_id": instagram_connection.external_account_id,
        "image_url": "https://img/1.jpg",
        "caption": "hello",
    }
    assert execute.call_args_list[2].args[1] == {
        "ig_user_id": instagram_connection.external_account_id,
        "creation_id": "container-1",
    }


def test_kill_switch_blocks_publishing(instagram_connection):
    instagram_connection.business.publishing_paused = True
    instagram_connection.business.save()

    with patch("growth.services.publishing.execute_tool") as execute:
        with pytest.raises(PublishingPaused):
            publish_image_post(
                instagram_connection, caption="x", image_url="https://img/3.jpg"
            )

    execute.assert_not_called()


def test_kill_switch_is_read_from_the_database_not_the_passed_instance(
    instagram_connection,
):
    """A worker holding a stale instance must still honour a just-flipped switch."""
    type(instagram_connection).objects.filter(pk=instagram_connection.pk).update(
        status=ConnectionStatus.HEALTHY
    )
    instagram_connection.business.__class__.objects.filter(
        pk=instagram_connection.business.pk
    ).update(publishing_paused=True)

    # The in-memory copy still says "running".
    assert instagram_connection.business.publishing_paused is False

    with pytest.raises(PublishingPaused):
        publish_image_post(
            instagram_connection, caption="x", image_url="https://img/4.jpg"
        )


def test_unhealthy_connection_blocks_publishing(instagram_connection):
    instagram_connection.status = ConnectionStatus.NEEDS_REAUTH
    instagram_connection.save()

    with pytest.raises(PublishingPaused):
        publish_image_post(
            instagram_connection, caption="x", image_url="https://img/5.jpg"
        )


def test_missing_container_id_is_an_error_not_a_silent_publish(instagram_connection):
    side_effect = fake_tool_responses(**{tools.IG_CREATE_MEDIA_CONTAINER: {}})

    with patch("growth.services.publishing.execute_tool", side_effect=side_effect):
        with pytest.raises(ToolExecutionError):
            publish_image_post(
                instagram_connection, caption="x", image_url="https://img/6.jpg"
            )


def test_quota_at_cap_raises(instagram_connection):
    at_cap = {"data": [{"quota_usage": 49, "config": {"quota_total": 50}}]}

    with patch("growth.services.publishing.execute_tool", return_value=at_cap):
        with pytest.raises(QuotaExhausted):
            ensure_instagram_quota(instagram_connection)


def test_unreadable_quota_does_not_block_publishing(instagram_connection):
    with patch("growth.services.publishing.execute_tool", return_value={"weird": True}):
        ensure_instagram_quota(instagram_connection)  # must not raise


def test_failed_quota_lookup_does_not_block_publishing(instagram_connection):
    error = ToolExecutionError(tools.IG_PUBLISHING_LIMIT, "boom")

    with patch("growth.services.publishing.execute_tool", side_effect=error):
        ensure_instagram_quota(instagram_connection)  # must not raise
