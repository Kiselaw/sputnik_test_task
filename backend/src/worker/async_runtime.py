from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any, TypeVar

from src.db.session import dispose_async_db, init_async_db


T = TypeVar("T")

_worker_loop: asyncio.AbstractEventLoop | None = None


def init_worker_async_runtime() -> None:
    """Initialize one async runtime for the current Celery worker process."""
    global _worker_loop
    if _worker_loop is not None and not _worker_loop.is_closed():
        return

    _worker_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_worker_loop)
    init_async_db()


def get_worker_loop() -> asyncio.AbstractEventLoop:
    """Return the Celery worker process event loop."""
    if _worker_loop is None or _worker_loop.is_closed():
        init_worker_async_runtime()
    if _worker_loop is None:
        raise RuntimeError("Celery worker event loop was not initialized")
    return _worker_loop


def run_async(coroutine: Coroutine[Any, Any, T]) -> T:
    """Run a coroutine on the worker process event loop."""
    loop = get_worker_loop()
    if loop.is_running():
        raise RuntimeError("Celery worker event loop is already running")
    return loop.run_until_complete(coroutine)


def shutdown_worker_async_runtime() -> None:
    """Dispose async resources and close the worker process event loop."""
    global _worker_loop
    if _worker_loop is None:
        return

    loop = _worker_loop
    _worker_loop = None

    if loop.is_closed():
        return

    try:
        loop.run_until_complete(dispose_async_db())
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.run_until_complete(loop.shutdown_default_executor())
    finally:
        loop.close()
        asyncio.set_event_loop(None)
