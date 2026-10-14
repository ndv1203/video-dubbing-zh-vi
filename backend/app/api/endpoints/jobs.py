import os
import re
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.job import ProcessingJob
from app.schemas.job import JobDetailResponse, JobResponse
from app.worker.tasks import process_demo_job

router = APIRouter()

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
CHUNK_SIZE = 1024 * 1024  # 1MB


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name
    # Keep alphanumeric, dot, underscore, hyphen
    cleaned = re.sub(r"[^\w\.-]", "_", name)
    return cleaned or "video.mp4"


@router.post(
    "",
    response_model=JobDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a video to dub",
)
async def upload_job(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tên tệp không hợp lệ",
        )

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Định dạng không được hỗ trợ ({ext}). Cho phép: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    safe_name = sanitize_filename(file.filename)
    job_id = uuid.uuid4()

    upload_dir = Path(settings.storage_root) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    destination_path = upload_dir / f"{job_id}_{safe_name}"

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    total_bytes = 0

    try:
        with open(destination_path, "wb") as buffer:
            while chunk := await file.read(CHUNK_SIZE):
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Dung lượng video vượt quá giới hạn cho phép ({settings.max_upload_size_mb}MB)",
                    )
                buffer.write(chunk)
    except HTTPException:
        if destination_path.exists():
            destination_path.unlink()
        raise
    except Exception as exc:
        if destination_path.exists():
            destination_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không thể lưu file: {str(exc)}",
        )

    job = ProcessingJob(
        id=job_id,
        status="queued",
        stage=None,
        progress=0,
        original_filename=file.filename,
        file_size_bytes=total_bytes,
        input_path=str(destination_path),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Đẩy tác vụ vào Celery queue
    process_demo_job.delay(str(job.id))

    return job


@router.get(
    "",
    response_model=list[JobResponse],
    summary="List recent dubbing jobs",
)
def list_jobs(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    stmt = (
        select(ProcessingJob)
        .order_by(desc(ProcessingJob.created_at))
        .offset(offset)
        .limit(min(limit, 100))
    )
    return db.scalars(stmt).all()


@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
    summary="Get dubbing job details",
)
def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
):
    job = db.get(ProcessingJob, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job không tồn tại",
        )
    return job


@router.get(
    "/{job_id}/stream",
    summary="Stream video (input or rendered output)",
)
def stream_job_video(
    job_id: UUID,
    kind: str = "output",  # 'output' or 'input'
    db: Session = Depends(get_db),
):
    job = db.get(ProcessingJob, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job không tồn tại",
        )

    target_path = job.output_path if kind == "output" else job.input_path
    if not target_path or not os.path.exists(target_path):
        # Fallback to input if output not available yet
        if job.input_path and os.path.exists(job.input_path):
            target_path = job.input_path
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tệp video chưa sẵn sàng hoặc không tồn tại",
            )

    return FileResponse(
        path=target_path,
        media_type="video/mp4",
        filename=Path(target_path).name,
    )

