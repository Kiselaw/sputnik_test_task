import logging

from celery.signals import worker_process_init, worker_process_shutdown

from src.worker.async_runtime import (
    init_worker_async_runtime,
    shutdown_worker_async_runtime,
)


logger = logging.getLogger(__name__)


@worker_process_init.connect
def init_worker_process_async_runtime(**kwargs) -> None:
    """Initialize async runtime after a Celery child process starts."""
    logger.info("Initializing Celery worker async runtime")
    init_worker_async_runtime()


@worker_process_shutdown.connect
def shutdown_worker_process_async_runtime(**kwargs) -> None:
    """Shutdown async runtime before a Celery child process exits."""
    logger.info("Shutting down Celery worker async runtime")
    shutdown_worker_async_runtime()
