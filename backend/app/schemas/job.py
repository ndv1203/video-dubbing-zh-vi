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


class JobDetailResponse(JobResponse):
    file_size_bytes: int
    duration_seconds: int | None = None
    input_path: str
    output_path: str | None = None
    subtitle_path: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    updated_at: datetime
