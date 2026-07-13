from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertItem(BaseModel):
    """Response schema for file alerts."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    file_id: str
    level: str
    message: str
    created_at: datetime
