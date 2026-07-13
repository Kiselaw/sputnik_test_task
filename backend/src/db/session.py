from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import settings


_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def init_async_db() -> None:
    """Initialize the async engine and session factory if needed."""
    global _engine, _session_maker
    if _engine is not None and _session_maker is not None:
        return

    _engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    _session_maker = async_sessionmaker(_engine, expire_on_commit=False)


async def dispose_async_db() -> None:
    """Dispose the async engine and reset database globals."""
    global _engine, _session_maker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_maker = None


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Return the initialized async session factory."""
    if _session_maker is None:
        init_async_db()
    if _session_maker is None:
        raise RuntimeError("Async database session maker was not initialized")
    return _session_maker


async def get_async_session() -> AsyncIterator[AsyncSession]:
    """Yield an async database session for FastAPI dependencies."""
    async with get_session_maker()() as session:
        yield session
