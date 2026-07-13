#!/bin/sh
set -eu

celery \
  -A src.worker.celery_app:celery_app \
  flower \
  --loglevel="${CELERY_LOGLEVEL:-info}" \
  --address="${FLOWER_HOST:-0.0.0.0}" \
  --port="${FLOWER_PORT:-5555}" \
  --basic_auth="${FLOWER_USER:-admin}:${FLOWER_PASSWORD:-admin}" &

exec celery \
  -A src.worker.celery_app:celery_app worker \
  -n file-processing-worker@%h \
  -Q "${FILE_PROCESSING_QUEUE:-file-processing}" \
  -l "${CELERY_LOGLEVEL:-info}"
