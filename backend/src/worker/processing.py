from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.alerts.repository import AlertRepository
from src.app.files.constants import AlertLevel, ProcessingStatus, ScanStatus
from src.app.files.repository import FileRepository
from src.core.config import settings
from src.core.errors import NotFoundError
from src.db.models import Alert, StoredFile
from src.db.session import get_session_maker
from src.worker.metadata import _extract_file_metadata


def _scan_file_for_threats(file_item: StoredFile) -> list[str]:
    """Return scan reasons for suspicious files."""
    reasons: list[str] = []
    extension = Path(file_item.original_name).suffix.lower()

    if extension in settings.suspicious_file_extensions:
        reasons.append(f"suspicious extension {extension}")

    if file_item.size > settings.max_safe_file_size_bytes:
        reasons.append(f"file is larger than {settings.max_safe_file_size_bytes} bytes")

    if extension == ".pdf" and file_item.mime_type not in {
        "application/pdf",
        "application/octet-stream",
    }:
        reasons.append("pdf extension does not match mime type")

    return reasons


def _build_processing_alert(file_item: StoredFile) -> Alert:
    """Build an alert that matches the final processing state."""
    if file_item.processing_status == ProcessingStatus.FAILED.value:
        return Alert(
            file_id=file_item.id,
            level=AlertLevel.CRITICAL.value,
            message="File processing failed",
        )

    if file_item.requires_attention:
        return Alert(
            file_id=file_item.id,
            level=AlertLevel.WARNING.value,
            message=f"File requires attention: {file_item.scan_details}",
        )

    return Alert(
        file_id=file_item.id,
        level=AlertLevel.INFO.value,
        message="File processed successfully",
    )


async def _commit_processing_alert(
    session: AsyncSession, file_item: StoredFile
) -> None:
    """Persist the final processing alert."""
    AlertRepository(session).add(_build_processing_alert(file_item))
    await session.commit()


async def process_uploaded_file(file_id: str) -> None:
    """Process an uploaded file and create a final alert."""
    async with get_session_maker()() as session:
        file_item = await FileRepository(session).get(file_id)
        if file_item is None:
            return

        file_item.processing_status = ProcessingStatus.PROCESSING.value
        reasons = _scan_file_for_threats(file_item)
        file_item.scan_status = (
            ScanStatus.SUSPICIOUS.value if reasons else ScanStatus.CLEAN.value
        )
        file_item.scan_details = ", ".join(reasons) if reasons else "no threats found"
        file_item.requires_attention = bool(reasons)
        await session.commit()

    async with get_session_maker()() as session:
        file_item = await FileRepository(session).get(file_id)
        if file_item is None:
            return

        try:
            file_item.metadata_json = await _extract_file_metadata(file_item)
            file_item.processing_status = ProcessingStatus.PROCESSED.value
        except NotFoundError:
            file_item.processing_status = ProcessingStatus.FAILED.value
            file_item.scan_status = file_item.scan_status or ScanStatus.FAILED.value
            file_item.scan_details = "stored file not found during metadata extraction"

        await session.commit()

    async with get_session_maker()() as session:
        file_item = await FileRepository(session).get(file_id)
        if file_item is not None:
            await _commit_processing_alert(session, file_item)
