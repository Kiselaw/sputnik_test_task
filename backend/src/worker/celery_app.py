"""Celery worker entrypoint used by the Celery CLI."""

from src.core.celery import celery_app
from src.worker import tasks as _tasks  # noqa: F401

__all__ = ["celery_app"]
