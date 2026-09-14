#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
CHECK_PROJECT="turbo-check-$$"
CHECK_STATUS=0
CHECK_NUMBER=0
CHECK_LOG_DIR="$(mktemp -d "${TMPDIR:-/tmp}/turbo-check.XXXXXX")"

compose() {
    docker compose -p "$CHECK_PROJECT" -f docker-compose.check.yaml --profile checks "$@"
}

cleanup() {
    if ! compose down --volumes --remove-orphans --rmi local > "$CHECK_LOG_DIR/cleanup.log" 2>&1; then
        printf 'WARN: cleanup failed; see cleanup.log\n'
    fi
    printf 'Full logs: %s\n' "$CHECK_LOG_DIR"
}

check() {
    local label="$1"
    shift
    CHECK_NUMBER=$((CHECK_NUMBER + 1))
    local log_file="$CHECK_LOG_DIR/$CHECK_NUMBER.log"
    local exit_code=0
    printf '%s: %s\n' "$CHECK_NUMBER" "$label" >> "$CHECK_LOG_DIR/index.txt"
    if "$@" > "$log_file" 2>&1; then
        printf 'PASS: %s\n' "$label"
    else
        exit_code=$?
        printf 'FAIL: %s\n' "$label"
        CHECK_STATUS=1
    fi
    python3 scripts/check_output.py "$log_file" "$exit_code"
}

report() {
    local label="$1"
    shift
    local log_file="$CHECK_LOG_DIR/report-$CHECK_NUMBER.log"
    CHECK_NUMBER=$((CHECK_NUMBER + 1))
    printf '%s: %s\n' "$(basename "$log_file")" "$label" >> "$CHECK_LOG_DIR/index.txt"
    if "$@" > "$log_file" 2>&1; then
        printf 'PASS: %s\n' "$label"
    else
        printf 'FAIL: %s\n' "$label"
        CHECK_STATUS=1
    fi
    python3 scripts/check_output.py "$log_file" 0
    if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
        { printf '\n### %s\n\n```text\n' "$label"; cat "$log_file"; printf '\n```\n'; } >> "$GITHUB_STEP_SUMMARY"
    fi
}

require_check() {
    check "$@"
    test "$CHECK_STATUS" -eq 0
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

require_check 'Compose configuration' compose config --quiet
require_check 'API and web builds' compose build api web frontend-check
require_check 'container health' compose up -d --wait --wait-timeout 180 db redis api web
require_check 'test dependencies' compose exec -T api uv sync --frozen

check 'Django system checks' compose exec -T api python manage.py check
check 'missing migrations' compose exec -T api python manage.py makemigrations --check --dry-run
check 'unapplied migrations' compose exec -T api python manage.py migrate --check
check 'backend tests' compose exec -T api pytest
check 'Python lint' compose exec -T api ruff check --no-fix .
check 'Python formatting' compose exec -T api ruff format --check .
check 'TypeScript' compose run --rm --no-deps frontend-check pnpm --filter web exec tsc --noEmit
check 'frontend validation tests' compose run --rm --no-deps frontend-check pnpm --filter web test
check 'frontend lint and formatting' compose run --rm --no-deps frontend-check pnpm exec biome check .
check 'Python dependency audit' compose exec -T api pip-audit
check 'frontend dependency audit' compose run --rm --no-deps frontend-check pnpm audit --audit-level high

report 'Python outdated packages' python3 scripts/dependency_report.py Python \
    docker compose -p "$CHECK_PROJECT" -f docker-compose.check.yaml exec -T api uv pip list --outdated --format json
report 'Frontend outdated packages' python3 scripts/dependency_report.py Frontend \
    docker compose -p "$CHECK_PROJECT" -f docker-compose.check.yaml run --rm --no-deps frontend-check pnpm outdated -r --format json
report 'Code and file counts' python3 scripts/code_metrics.py

exit "$CHECK_STATUS"
