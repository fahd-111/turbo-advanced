"""Composio tool slugs, in one place.

Slugs and argument names were verified against a live Composio project on
2026-08-06 with:

    docker compose exec api uv run python manage.py composio_tools \
        INSTAGRAM_POST_IG_USER_MEDIA INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH

Re-run that after any Composio toolkit update. If a name changes, correct it
here and nothing else needs to change.

Two quirks worth remembering:
  * Instagram captions want hashtags URL encoded ("#" as "%23"). Phase 3 has to
    handle this when it starts generating hashtag sets.
  * Facebook's caption property is "message"; "caption" is accepted but is not
    declared in the schema.
"""

# --- Instagram (Business/Creator accounts only) ------------------------------
# Publishing is a two step container -> publish flow.
IG_CREATE_MEDIA_CONTAINER = "INSTAGRAM_POST_IG_USER_MEDIA"
IG_PUBLISH_MEDIA = "INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH"
IG_PUBLISHING_LIMIT = "INSTAGRAM_GET_IG_USER_CONTENT_PUBLISHING_LIMIT"
# Accepts ig_user_id="me", so it is the only way to learn our own account id
# without already knowing it.
IG_GET_USER_INFO = "INSTAGRAM_GET_USER_INFO"
SELF = "me"

# --- Facebook (Pages only) ---------------------------------------------------
FB_CREATE_PHOTO_POST = "FACEBOOK_CREATE_PHOTO_POST"
FB_CREATE_POST = "FACEBOOK_CREATE_POST"
FB_LIST_MANAGED_PAGES = "FACEBOOK_LIST_MANAGED_PAGES"
FB_GET_PAGE_DETAILS = "FACEBOOK_GET_PAGE_DETAILS"
