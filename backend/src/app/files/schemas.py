from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FileItem(BaseModel):
    """Response schema for uploaded files."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    original_name: str
    mime_type: str
    size: int
    processing_status: str
    scan_status: str | None
    scan_details: str | None
    metadata_json: dict | None
    requires_attention: bool
    created_at: datetime
    updated_at: datetime


class FileUpdate(BaseModel):
    """Request schema for file title updates."""

    title: str = Field(min_length=1, max_length=255)
