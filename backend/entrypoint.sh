#!/bin/bash
set -e

if [ "${1:-}" = "gunicorn" ]; then
    python manage.py check
    python manage.py migrate --noinput
fi

exec "$@"
