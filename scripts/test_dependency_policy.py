import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from io import StringIO

from dependency_policy import apply_version_policy, select_eligible_version


class DependencyPolicyTest(unittest.TestCase):
    def test_release_age_does_not_accept_an_older_eligible_version(self):
        published = {
            "4.6.3": "2026-09-10T00:00:00Z",
            "4.6.4": "2026-09-12T00:00:00Z",
            "4.6.5": "2026-09-13T18:00:00Z",
            "5.0.0-beta.1": "2026-09-10T00:00:00Z",
        }
        now = datetime(2026, 9, 14, 8, tzinfo=timezone.utc)
        self.assertEqual(select_eligible_version(published, "4.6.5", now), "4.6.4")

    def test_only_approved_redis_version_is_exempt(self):
        packages = [
            {"name": "redis", "version": "6.4.0", "latest_version": "8.1.0"},
            {"name": "django", "version": "5.1.4", "latest_version": "6.1.1"},
        ]
        with redirect_stdout(StringIO()):
            self.assertEqual(apply_version_policy("Python", packages), packages[1:])
        older = [{"name": "redis", "version": "6.3.0", "latest_version": "8.1.0"}]
        self.assertEqual(apply_version_policy("Python", older), older)


if __name__ == "__main__":
    unittest.main()
