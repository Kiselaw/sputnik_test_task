from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import StoredFile


class FileRepository:
    """Persist and query stored files."""

    def __init__(self, session: AsyncSession) -> None:
        """Store the request-scoped database session."""
        self.session = session

    async def list(self) -> list[StoredFile]:
        """Return files ordered by creation time."""
        result = await self.session.execute(
            select(StoredFile).order_by(StoredFile.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, file_id: str) -> StoredFile | None:
        """Return a file by primary key."""
        return await self.session.get(StoredFile, file_id)

    def add(self, file_item: StoredFile) -> None:
        """Add a file row to the current session."""
        self.session.add(file_item)

    async def delete(self, file_item: StoredFile) -> None:
        """Delete a file row from the current session."""
        await self.session.delete(file_item)
