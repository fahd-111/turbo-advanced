from urllib.parse import parse_qs, urlparse

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from growth.models import Business, ConnectionStatus, Platform, SocialConnection
from growth.services import connections as connection_service

User = get_user_model()


def callback_token(connection: SocialConnection) -> str:
    """The token as Django would hand it to the view, i.e. percent-decoded."""
    query = urlparse(connection_service.callback_url(connection)).query
    return parse_qs(query)["token"][0]


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def owner(db):
    return User.objects.create_user(username="owner@example.com", password="pw-12345!x")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="other@example.com", password="pw-12345!x")


@pytest.fixture
def business(owner):
    return Business.objects.create(
        owner=owner, name="Acme Coffee", timezone="Europe/Berlin"
    )


@pytest.fixture
def other_business(other_user):
    return Business.objects.create(owner=other_user, name="Rival Tea")


@pytest.fixture
def instagram_connection(business):
    return SocialConnection.objects.create(
        business=business,
        platform=Platform.INSTAGRAM,
        composio_connected_account_id="ca_ig_123",
        external_account_id="17841400000000000",
        status=ConnectionStatus.HEALTHY,
    )


@pytest.fixture
def facebook_connection(business):
    return SocialConnection.objects.create(
        business=business,
        platform=Platform.FACEBOOK,
        composio_connected_account_id="ca_fb_123",
        external_account_id="998877665544",
        status=ConnectionStatus.HEALTHY,
    )
