from celery import shared_task

from src.core.config import settings
from src.worker import signals as _lifecycle  # noqa: F401
from src.worker.async_runtime import run_async
from src.worker.processing import process_uploaded_file


@shared_task(
    name=settings.process_uploaded_file_task_name, queue=settings.file_processing_queue
)
def process_uploaded_file_task(file_id: str) -> None:
    """Run uploaded file processing inside the worker async runtime."""
    run_async(process_uploaded_file(file_id))
