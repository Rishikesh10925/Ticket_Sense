#!/bin/sh
# Runs migrations before the API starts — Render (and most PaaS hosts) just run
# this container's CMD directly, with no separate "release phase" step the way
# docker-compose's local dev flow assumes migrations are applied manually.
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
