import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from check_output import MAX_DIAGNOSTICS, summarize_output


class CheckOutputTest(unittest.TestCase):
    def test_runner_preserves_failure_and_saves_full_logs(self):
        with tempfile.TemporaryDirectory() as directory:
            docker = Path(directory) / "docker"
            docker.write_text(
                '#!/bin/sh\necho "Download progress hidden"\n'
                'case "$*" in *pip-audit*) echo "Found 2 vulnerabilities"; exit 1;; esac\n'
            )
            docker.chmod(0o755)
            result = subprocess.run(
                ["bash", str(Path(__file__).with_name("check.sh"))],
                check=False,
                env={
                    **os.environ,
                    "PATH": directory + os.pathsep + os.environ["PATH"],
                    "TMPDIR": directory,
                },
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("FAIL: Python dependency audit", result.stdout)
            self.assertIn("Found 2 vulnerabilities", result.stdout)
            self.assertNotIn("Download progress hidden", result.stdout)
            self.assertTrue(tuple(Path(directory).glob("turbo-check.*/cleanup.log")))

    def test_output_is_bounded_and_keeps_diagnostics(self):
        self.assertEqual(summarize_output("Downloading packages\nReady", False), "")
        self.assertIn(
            "WARN slow download", summarize_output("WARN slow download", False)
        )
        self.assertIn("command not found", summarize_output("command not found", True))
        errors = "\n".join(f"error TS{number}: broken" for number in range(20))
        self.assertEqual(
            len(summarize_output(errors, True).splitlines()), MAX_DIAGNOSTICS
        )
        self.assertNotIn("\x1b", summarize_output("\x1b[31mERROR\x1b[0m", True))


if __name__ == "__main__":
    unittest.main()
