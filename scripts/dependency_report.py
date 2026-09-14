"""Report available upgrades and fail when dependencies are outdated."""

import json
import subprocess
import sys

from dependency_policy import apply_version_policy


def summarize_versions(packages):
    if isinstance(packages, list):
        return [
            f"{item['name']}: {item['version']} -> {item['latest_version']}"
            for item in packages
        ]
    return [
        f"{name}: {item.get('current', 'missing')} -> {item['latest']}"
        for name, item in sorted(packages.items())
    ]


def report_versions(label, command):
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=180, check=False
    )
    try:
        if result.returncode not in (0, 1):
            raise ValueError("version command failed")
        packages = json.loads(result.stdout)
        original_versions = summarize_versions(packages)
        if result.returncode and not original_versions:
            raise ValueError("version command failed without results")
        versions = summarize_versions(apply_version_policy(label, packages))
    except (ValueError, TypeError, KeyError, AttributeError):
        print(f"ERROR: {label} version report unavailable; see full log")
        print(result.stdout, result.stderr)
        return 1
    print(f"INFO: {label}: {len(versions)} outdated packages")
    print("\n".join(f"INFO: {version}" for version in versions))
    return int(bool(versions))


if __name__ == "__main__":
    try:
        sys.exit(report_versions(sys.argv[1], sys.argv[2:]))
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"ERROR: version report unavailable: {error}")
        sys.exit(1)
