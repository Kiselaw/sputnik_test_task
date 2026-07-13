from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork:
    """Manage transaction operations for one database session."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the request-scoped database session."""
        self.session = session

    async def commit(self) -> None:
        """Commit the current database transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback the current database transaction."""
        await self.session.rollback()

    async def refresh(self, instance: object) -> None:
        """Refresh an ORM instance from the database."""
        await self.session.refresh(instance)
