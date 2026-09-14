"""Approved compatibility and release-age exceptions; security audits stay strict."""

import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from urllib.request import urlopen

MINIMUM_RELEASE_AGE = timedelta(hours=24)
STABLE_VERSION = re.compile(r"^\d+\.\d+\.\d+$")


def version_numbers(version):
    return tuple(map(int, version.split(".")))


def select_eligible_version(published, latest, now):
    cutoff = now - MINIMUM_RELEASE_AGE
    candidates = [
        version
        for version, date in published.items()
        if STABLE_VERSION.fullmatch(version)
        and version_numbers(version) <= version_numbers(latest)
        and datetime.fromisoformat(date.replace("Z", "+00:00")) <= cutoff
    ]
    return max(candidates, key=version_numbers)


def eligible_frontend_package(name, item):
    with urlopen(
        f"https://registry.npmjs.org/{quote(name, safe='')}", timeout=15
    ) as response:
        metadata = json.load(response)
    latest = select_eligible_version(
        metadata["time"], item["latest"], datetime.now(timezone.utc)
    )
    if latest != item["latest"]:
        print(
            f"INFO: {name}: {item['latest']} deferred by 24-hour policy; eligible {latest}"
        )
    return {**item, "latest": latest}


def apply_version_policy(label, packages):
    if label == "Python":
        # Approved: Kombu 5.6.2's Redis extra requires redis<6.5.
        deferred = [
            item
            for item in packages
            if item["name"] == "redis" and item["version"] == "6.4.0"
        ]
        if deferred:
            print(
                "INFO: redis 6.4.0 retained: Celery/Kombu requires redis<6.5; security audit enforced"
            )
        return [item for item in packages if item not in deferred]
    if label != "Frontend":
        return packages
    eligible = {
        name: eligible_frontend_package(name, item) for name, item in packages.items()
    }
    return {
        name: item
        for name, item in eligible.items()
        if item["current"] != item["latest"]
    }
