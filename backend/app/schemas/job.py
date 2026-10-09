from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobResponse(BaseModel):
    id: UUID
    status: str
    stage: str | None
    progress: int
    original_filename: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
