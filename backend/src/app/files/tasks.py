from celery import shared_task

from src.core.config import settings


@shared_task(
    name=settings.process_uploaded_file_task_name, queue=settings.file_processing_queue
)
def process_uploaded_file_task(file_id: str) -> None:
    """Declare the task signature used by the API to enqueue processing."""
    pass
