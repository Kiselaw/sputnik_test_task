from __future__ import annotations

import asyncio
from pathlib import Path

from src.app.files.storage import FileStorage
from src.core.config import settings
from src.db.models import StoredFile


PDF_PAGE_MARKER = b"/Type /Page"


def _read_text_stats(path: Path) -> tuple[int, int]:
    """Read text file statistics without loading the full file."""
    line_count = 0
    char_count = 0
    last_char = ""

    with path.open("r", encoding="utf-8", errors="ignore") as file_obj:
        while chunk := file_obj.read(settings.upload_chunk_size_bytes):
            char_count += len(chunk)
            line_count += chunk.count("\n")
            last_char = chunk[-1]

    if char_count > 0 and last_char != "\n":
        line_count += 1

    return line_count, char_count


def _estimate_pdf_pages(path: Path) -> int:
    """Estimate PDF page count by scanning page markers."""
    count = 0
    tail = b""
    marker_tail_size = len(PDF_PAGE_MARKER) - 1

    with path.open("rb") as file_obj:
        while chunk := file_obj.read(settings.upload_chunk_size_bytes):
            data = tail + chunk
            count += data.count(PDF_PAGE_MARKER)
            tail = data[-marker_tail_size:]

    return max(count, 1)


async def _extract_file_metadata(
    file_item: StoredFile,
    storage: FileStorage | None = None,
) -> dict:
    """Extract basic metadata for a stored file."""
    storage = storage or FileStorage(settings.storage_dir)
    stored_path = await storage.ensure_exists(file_item.stored_name)
    metadata = {
        "extension": Path(file_item.original_name).suffix.lower(),
        "size_bytes": file_item.size,
        "mime_type": file_item.mime_type,
    }

    if file_item.mime_type.startswith("text/"):
        line_count, char_count = await asyncio.to_thread(_read_text_stats, stored_path)
        metadata["line_count"] = line_count
        metadata["char_count"] = char_count
    elif file_item.mime_type == "application/pdf":
        metadata["approx_page_count"] = await asyncio.to_thread(
            _estimate_pdf_pages, stored_path
        )

    return metadata
