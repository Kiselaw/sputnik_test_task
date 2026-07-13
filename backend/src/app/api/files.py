from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from starlette import status

from src.app.files.schemas import FileItem, FileUpdate
from src.app.files.service import FileService
from src.app.api.dependencies import get_file_service
from src.app.files.tasks import process_uploaded_file_task


router = APIRouter(prefix="/files", tags=["Files"])


@router.get("/", response_model=list[FileItem])
async def list_files_view(service: FileService = Depends(get_file_service)):
    """Return all uploaded files."""
    return await service.list_files()


@router.post("/", response_model=FileItem, status_code=status.HTTP_201_CREATED)
async def create_file_view(
    title: str = Form(...),
    file: UploadFile = File(...),
    service: FileService = Depends(get_file_service),
):
    """Create a file record and enqueue background processing."""
    file_item = await service.create_file(title=title, upload_file=file)
    process_uploaded_file_task.delay(file_item.id)
    return file_item


@router.get("/{file_id}", response_model=FileItem)
async def get_file_view(file_id: str, service: FileService = Depends(get_file_service)):
    """Return one uploaded file by id."""
    return await service.get_file(file_id)


@router.patch("/{file_id}", response_model=FileItem)
async def update_file_view(
    file_id: str,
    payload: FileUpdate,
    service: FileService = Depends(get_file_service),
):
    """Update a file title."""
    return await service.update_file(file_id=file_id, title=payload.title)


@router.get("/{file_id}/download")
async def download_file(file_id: str, service: FileService = Depends(get_file_service)):
    """Download a stored file by id."""
    file_item, stored_path = await service.get_file_download(file_id)
    return FileResponse(
        path=stored_path,
        media_type=file_item.mime_type,
        filename=file_item.original_name,
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file_view(
    file_id: str, service: FileService = Depends(get_file_service)
):
    """Delete a file and its related data."""
    await service.delete_file(file_id)
