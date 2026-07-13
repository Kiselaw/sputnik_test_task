#!/bin/sh
set -eu

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  alembic upgrade head
fi

if [ "${WEB_RELOAD:-0}" = "1" ]; then
  exec uvicorn src.app.main:app --host "${WEB_HOST:-0.0.0.0}" --port "${WEB_PORT:-8000}" --reload
fi

exec uvicorn src.app.main:app --host "${WEB_HOST:-0.0.0.0}" --port "${WEB_PORT:-8000}"
