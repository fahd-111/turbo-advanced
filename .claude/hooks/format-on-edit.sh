#!/bin/sh
# Formats any file Claude edits, so formatting is never a review topic.
file=$(cat | jq -r '.tool_input.file_path // empty')
[ -z "$file" ] && exit 0
case "$file" in
  *.ts|*.tsx|*.js|*.jsx|*.json)
    (cd frontend && pnpm exec biome check --write "$file") >/dev/null 2>&1 ;;
  *.py)
    (cd backend && uv run -- ruff format "$file" && uv run -- ruff check --fix "$file") >/dev/null 2>&1 ;;
esac
exit 0
