import pytest
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.test import Client
from django.urls import reverse

PASSWORD = "correct-horse-battery-42"
WEB_ORIGIN = "http://localhost:3000"


@pytest.fixture
def session_client(db):
    get_user_model().objects.create_user(username="session-user", password=PASSWORD)
    return Client(enforce_csrf_checks=True, HTTP_ORIGIN=WEB_ORIGIN)


def login_client(client, **credentials):
    csrf = client.get(reverse("auth-csrf")).json()["csrfToken"]
    return client.post(
        reverse("auth-login"),
        {"username": "session-user", "password": PASSWORD, **credentials},
        HTTP_X_CSRFTOKEN=csrf,
    )


@pytest.mark.django_db
def test_registered_user_can_login_immediately():
    client = Client(enforce_csrf_checks=True, HTTP_ORIGIN=WEB_ORIGIN)
    response = client.post(
        reverse("api-users-list"),
        {"username": "new-signup", "password": PASSWORD, "password_retype": PASSWORD},
        content_type="application/json",
    )
    assert response.status_code == 201
    assert get_user_model().objects.get(username="new-signup").is_active
    assert login_client(client, username="new-signup").status_code == 200
    assert client.get(reverse("api-users-me")).json()["username"] == "new-signup"


def test_session_login_csrf_and_logout(session_client):
    client = session_client
    assert client.get(reverse("api-users-me")).status_code == 403
    assert client.post(reverse("auth-login")).status_code == 403
    assert login_client(client, password="incorrect").status_code == 400
    response = login_client(client)
    assert response.status_code == 200
    assert response.cookies["sessionid"]["httponly"]
    assert client.get(reverse("api-users-me")).json()["username"] == "session-user"
    assert client.patch(reverse("api-users-me"), {}).status_code == 403
    csrf = client.cookies["csrftoken"].value
    assert client.patch(
        reverse("api-users-me"), {"first_name": "Updated"},
        content_type="application/json", HTTP_X_CSRFTOKEN=csrf,
    ).status_code == 200
    assert client.post(reverse("auth-logout")).status_code == 403
    session_key = client.cookies["sessionid"].value
    assert client.post(reverse("auth-logout"), HTTP_X_CSRFTOKEN=csrf).status_code == 200
    assert not Session.objects.filter(session_key=session_key).exists()
    client.cookies["sessionid"] = session_key
    assert client.get(reverse("api-users-me")).status_code == 403


def test_login_rejects_untrusted_origin_and_inactive_user(session_client):
    client = session_client
    csrf = client.get(reverse("auth-csrf")).json()["csrfToken"]
    assert client.post(
        reverse("auth-login"), {"username": "session-user", "password": PASSWORD},
        HTTP_X_CSRFTOKEN=csrf, HTTP_ORIGIN="https://untrusted.example",
    ).status_code == 403
    get_user_model().objects.filter(username="session-user").update(is_active=False)
    assert login_client(client).status_code == 400


def test_expired_session_is_rejected(session_client):
    login_client(session_client)
    session = session_client.session
    session.set_expiry(-1)
    session.save()
    assert session_client.get(reverse("api-users-me")).status_code == 403


def test_password_change_and_account_deletion_revoke_login(session_client):
    client = session_client
    login_client(client)
    other_client = Client(enforce_csrf_checks=True, HTTP_ORIGIN=WEB_ORIGIN)
    login_client(other_client)
    new_password = "another-strong-password-42"
    response = client.post(
        reverse("api-users-change-password"),
        {"password": PASSWORD, "password_new": new_password, "password_retype": new_password},
        content_type="application/json", HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )
    assert response.status_code == 204
    assert client.get(reverse("api-users-me")).status_code == 403
    assert other_client.get(reverse("api-users-me")).status_code == 403
    assert login_client(client, password=new_password).status_code == 200
    assert client.delete(
        reverse("api-users-delete-account"), HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    ).status_code == 204
    assert client.get(reverse("api-users-me")).status_code == 403
