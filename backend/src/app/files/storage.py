from __future__ import annotations

import asyncio
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from src.core.config import settings
from src.core.errors import NotFoundError, ValidationError


class UploadFileLike(Protocol):
    """Describe the upload object methods used by file storage."""

    filename: str | None
    content_type: str | None

    async def read(self, size: int = -1) -> bytes:
        """Read bytes from the upload stream."""
        ...


@dataclass(frozen=True)
class SavedUpload:
    """Describe a file saved on local storage."""

    original_name: str
    stored_name: str
    mime_type: str
    size: int


class FileStorage:
    """Store uploaded files on the local filesystem."""

    def __init__(self, base_dir: Path) -> None:
        """Create storage rooted at the given directory."""
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, stored_name: str) -> Path:
        """Build an absolute path for a stored file name."""
        return self.base_dir / stored_name

    async def save_upload(
        self, file_id: str, upload_file: UploadFileLike
    ) -> SavedUpload:
        """Stream an uploaded file to disk and return saved metadata."""
        original_name = upload_file.filename or file_id
        suffix = Path(original_name).suffix
        stored_name = f"{file_id}{suffix}"
        stored_path = self.path_for(stored_name)
        size = 0

        try:
            with stored_path.open("wb") as output:
                while chunk := await upload_file.read(settings.upload_chunk_size_bytes):
                    size += len(chunk)
                    await asyncio.to_thread(output.write, chunk)
                await asyncio.to_thread(output.flush)
        except Exception:
            await self.delete_if_exists(stored_name)
            raise

        if size == 0:
            await self.delete_if_exists(stored_name)
            raise ValidationError("File is empty")

        mime_type = (
            upload_file.content_type
            or mimetypes.guess_type(original_name)[0]
            or "application/octet-stream"
        )
        return SavedUpload(
            original_name=original_name,
            stored_name=stored_name,
            mime_type=mime_type,
            size=size,
        )

    async def ensure_exists(self, stored_name: str) -> Path:
        """Return a stored path or raise when the file is missing."""
        stored_path = self.path_for(stored_name)
        if not await asyncio.to_thread(stored_path.exists):
            raise NotFoundError("Stored file not found")
        return stored_path

    async def delete_if_exists(self, stored_name: str) -> None:
        """Delete a stored file if it exists."""
        stored_path = self.path_for(stored_name)
        await asyncio.to_thread(stored_path.unlink, missing_ok=True)
