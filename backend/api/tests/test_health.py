from unittest.mock import patch

import pytest
from django.test import RequestFactory, override_settings

from api.health import health_check


@pytest.mark.django_db
def test_health_reports_dependency_failure():
    request = RequestFactory().get("/health/")
    with override_settings(REDIS_URL=""):
        assert health_check(request).status_code == 200
    with patch("api.health.connection.cursor", side_effect=OSError):
        assert health_check(request).status_code == 503
    with override_settings(REDIS_URL="redis://redis:6379/0"):
        with patch("api.health.Redis.from_url", side_effect=OSError):
            assert health_check(request).status_code == 503
