from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.alerts.repository import AlertRepository
from src.app.alerts.service import AlertService
from src.app.files.repository import FileRepository
from src.app.files.service import FileService
from src.app.files.storage import FileStorage
from src.db.session import get_async_session
from src.db.unit_of_work import UnitOfWork


def get_file_storage(request: Request) -> FileStorage:
    """Return the FileStorage instance attached to the application."""
    return request.app.state.file_storage


def get_file_service(
    session: AsyncSession = Depends(get_async_session),
    storage: FileStorage = Depends(get_file_storage),
) -> FileService:
    """Build a request-scoped FileService."""
    return FileService(
        files_repo=FileRepository(session),
        alerts_repo=AlertRepository(session),
        storage=storage,
        uow=UnitOfWork(session),
    )


def get_alert_service(
    session: AsyncSession = Depends(get_async_session),
) -> AlertService:
    """Build a request-scoped AlertService."""
    return AlertService(alerts_repo=AlertRepository(session))
