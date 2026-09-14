import json
import subprocess
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from code_metrics import is_source_file
from dependency_report import report_versions


class DependencyReportTest(unittest.TestCase):
    def run_report(self, data, exit_code=0):
        result = subprocess.CompletedProcess([], exit_code, json.dumps(data), "")
        with (
            patch("dependency_report.subprocess.run", return_value=result),
            redirect_stdout(StringIO()),
        ):
            return report_versions("test", ["unused"])

    def test_outdated_and_failed_queries_block(self):
        self.assertEqual(self.run_report([]), 0)
        self.assertEqual(self.run_report({}), 0)
        self.assertEqual(
            self.run_report(
                [{"name": "django", "version": "5.1.4", "latest_version": "6.0"}]
            ),
            1,
        )
        self.assertEqual(
            self.run_report({"next": {"current": "16.0.10", "latest": "16.1.0"}}, 1), 1
        )
        self.assertEqual(self.run_report({"error": "offline"}, 1), 1)
        self.assertEqual(self.run_report({}, 2), 1)

    def test_metrics_exclude_generated_sources(self):
        self.assertTrue(is_source_file(Path("frontend/apps/web/app/page.tsx")))
        self.assertFalse(is_source_file(Path("frontend/apps/web/next-env.d.ts")))
        self.assertFalse(is_source_file(Path("frontend/.next/server.js")))
        self.assertFalse(is_source_file(Path("frontend/packages/types/api/index.ts")))


if __name__ == "__main__":
    unittest.main()
