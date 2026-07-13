from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Alert


class AlertRepository:
    """Persist and query file alerts."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the request-scoped database session."""
        self.session = session

    async def list(self) -> list[Alert]:
        """Return alerts ordered by creation time."""
        result = await self.session.execute(
            select(Alert).order_by(Alert.created_at.desc())
        )
        return list(result.scalars().all())

    def add(self, alert: Alert) -> None:
        """Add an alert to the current session."""
        self.session.add(alert)

    async def delete_by_file_id(self, file_id: str) -> None:
        """Delete alerts attached to a file."""
        await self.session.execute(delete(Alert).where(Alert.file_id == file_id))
