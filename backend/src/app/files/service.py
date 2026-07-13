from pathlib import Path
from uuid import uuid7

from src.app.alerts.repository import AlertRepository
from src.core.errors import NotFoundError, ValidationError
from src.db.models import StoredFile
from src.db.unit_of_work import UnitOfWork
from src.app.files.constants import ProcessingStatus
from src.app.files.repository import FileRepository
from src.app.files.storage import FileStorage, UploadFileLike


def _normalize_title(title: str) -> str:
    """Normalize and validate a file title."""
    normalized = title.strip()
    if not normalized:
        raise ValidationError("Title is required")
    if len(normalized) > 255:
        raise ValidationError("Title is too long")
    return normalized


class FileService:
    """Coordinate file use cases across storage and persistence."""

    def __init__(
        self,
        files_repo: FileRepository,
        alerts_repo: AlertRepository,
        storage: FileStorage,
        uow: UnitOfWork,
    ) -> None:
        """Store request-scoped repositories, UoW, and shared file storage."""
        self.files_repo = files_repo
        self.alerts_repo = alerts_repo
        self.storage = storage
        self.uow = uow

    async def list_files(self) -> list[StoredFile]:
        """Return stored files ordered by creation time."""
        return await self.files_repo.list()

    async def get_file(self, file_id: str) -> StoredFile:
        """Return one stored file or raise a domain not-found error."""
        file_item = await self.files_repo.get(file_id)
        if file_item is None:
            raise NotFoundError("File not found")
        return file_item

    async def create_file(self, title: str, upload_file: UploadFileLike) -> StoredFile:
        """Save an uploaded file and create its database row."""
        normalized_title = _normalize_title(title)
        file_id = str(uuid7())
        saved_file = await self.storage.save_upload(
            file_id=file_id, upload_file=upload_file
        )

        file_item = StoredFile(
            id=file_id,
            title=normalized_title,
            original_name=saved_file.original_name,
            stored_name=saved_file.stored_name,
            mime_type=saved_file.mime_type,
            size=saved_file.size,
            processing_status=ProcessingStatus.UPLOADED.value,
        )

        try:
            self.files_repo.add(file_item)
            await self.uow.commit()
        except Exception:
            await self.uow.rollback()
            await self.storage.delete_if_exists(saved_file.stored_name)
            raise

        await self.uow.refresh(file_item)
        return file_item

    async def update_file(self, file_id: str, title: str) -> StoredFile:
        """Update a file title."""
        file_item = await self.get_file(file_id)
        file_item.title = _normalize_title(title)
        try:
            await self.uow.commit()
        except Exception:
            await self.uow.rollback()
            raise

        await self.uow.refresh(file_item)
        return file_item

    async def delete_file(self, file_id: str) -> None:
        """Delete a file row, related alerts, and the stored file if present."""
        file_item = await self.get_file(file_id)
        stored_name = file_item.stored_name

        try:
            await self.alerts_repo.delete_by_file_id(file_id)
            await self.files_repo.delete(file_item)
            await self.uow.commit()
        except Exception:
            await self.uow.rollback()
            raise

        await self.storage.delete_if_exists(stored_name)

    async def get_file_download(self, file_id: str) -> tuple[StoredFile, Path]:
        """Return file metadata and a verified local path for download."""
        file_item = await self.get_file(file_id)
        stored_path = await self.storage.ensure_exists(file_item.stored_name)
        return file_item, stored_path
