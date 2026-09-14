#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
CHECK_PROJECT="turbo-check-$$"
CHECK_GROUP="${1:-all}"
case "$CHECK_GROUP" in
    all|build-api|build-web|health|migrations|test|lint|format|typecheck|security|outdated|metrics) ;;
    *) printf 'ERROR: unknown check group: %s\n' "$CHECK_GROUP" >&2; exit 2 ;;
esac
CHECK_STATUS=0
CHECK_NUMBER=0
CHECK_LOG_DIR="$(mktemp -d "${TMPDIR:-/tmp}/turbo-check.XXXXXX")"

compose() {
    docker compose -p "$CHECK_PROJECT" -f docker-compose.check.yaml --profile checks "$@"
}

cleanup() {
    if [ "$CHECK_GROUP" != metrics ] && ! compose down --volumes --remove-orphans --rmi local > "$CHECK_LOG_DIR/cleanup.log" 2>&1; then
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

selected() {
    [ "$CHECK_GROUP" = all ] || [ "$CHECK_GROUP" = "$1" ]
}

if [ "$CHECK_GROUP" != metrics ]; then
    require_check 'Compose configuration' compose config --quiet
    case "$CHECK_GROUP" in
        build-api) require_check 'API build' compose build api ;;
        build-web) require_check 'web build' compose build web ;;
        typecheck) require_check 'frontend build' compose build frontend-check ;;
        migrations) require_check 'API build' compose build api ;;
        health) require_check 'API and web builds' compose build api web ;;
        all) require_check 'API and web builds' compose build api web frontend-check ;;
        *) require_check 'check images' compose build api frontend-check ;;
    esac
    case "$CHECK_GROUP" in
        all|health) require_check 'container health' compose up -d --wait --wait-timeout 180 db redis api web ;;
        migrations|test|lint|format|security|outdated)
            require_check 'API health' compose up -d --wait --wait-timeout 180 db redis api ;;
    esac
    case "$CHECK_GROUP" in
        all|migrations|test|lint|format|security|outdated)
            require_check 'test dependencies' compose exec -T api uv sync --frozen ;;
    esac
fi

if selected migrations; then
    check 'Django system checks' compose exec -T api python manage.py check
    check 'missing migrations' compose exec -T api python manage.py makemigrations --check --dry-run
    check 'unapplied migrations' compose exec -T api python manage.py migrate --check
fi
if selected test; then
    check 'backend tests' compose exec -T api pytest
    check 'frontend validation tests' compose run --rm --no-deps frontend-check pnpm --filter web test
fi
if selected lint; then
    check 'Python lint' compose exec -T api ruff check --no-fix .
    check 'frontend lint' compose run --rm --no-deps frontend-check pnpm exec biome check --formatter-enabled=false .
fi
if selected format; then
    check 'Python formatting' compose exec -T api ruff format --check .
    check 'frontend formatting' compose run --rm --no-deps frontend-check pnpm exec biome format .
fi
if selected typecheck; then
    check 'TypeScript' compose run --rm --no-deps frontend-check pnpm --filter web exec tsc --noEmit
fi
if selected security; then
    check 'Python dependency audit' compose exec -T api pip-audit
    check 'frontend dependency audit' compose run --rm --no-deps frontend-check pnpm audit --audit-level high
fi
if selected outdated; then
    report 'Python outdated packages' python3 scripts/dependency_report.py Python \
        docker compose -p "$CHECK_PROJECT" -f docker-compose.check.yaml exec -T api uv pip list --outdated --format json
    report 'Frontend outdated packages' python3 scripts/dependency_report.py Frontend \
        docker compose -p "$CHECK_PROJECT" -f docker-compose.check.yaml run --rm --no-deps frontend-check pnpm outdated -r --format json
fi
if selected metrics; then
    report 'Code and file counts' python3 scripts/code_metrics.py
fi

exit "$CHECK_STATUS"
