import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.job import ProcessingJob
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)

_translator_instance = None


def get_translator():
    global _translator_instance
    if _translator_instance is None:
        try:
            from app.ml.translator import Translator

            model_dir = Path(settings.models_root) / "translator_zh_vi"
            logger.info(f"Loading translator model from {model_dir}...")
            _translator_instance = Translator.load_from_dir(
                model_dir=model_dir,
                checkpoint_name="best.pt",
                device="cpu",
            )
            logger.info("Translator model loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load translator model: {e}")
            return None
    return _translator_instance


@celery_app.task(name="app.worker.tasks.ping")
def ping():
    return {
        "status": "ok",
        "message": "Celery worker is running",
    }


@celery_app.task(
    bind=True,
    name="app.worker.tasks.process_demo_job",
)
def process_demo_job(self, job_id: str):
    job_uuid = UUID(job_id)

    with SessionLocal() as db:
        job = db.get(ProcessingJob, job_uuid)

        if job is None:
            raise ValueError(f"Job not found: {job_id}")

        if job.status == "completed":
            return {"job_id": job_id, "status": "completed"}

        job.status = "processing"
        job.started_at = datetime.now(timezone.utc)
        job.error_code = None
        job.error_message = None
        db.commit()

    try:
        from app.pipeline.orchestrator import run_dubbing_pipeline

        result = run_dubbing_pipeline(job_id=job_id)

        with SessionLocal() as db:
            job = db.get(ProcessingJob, job_uuid)
            if job:
                job.status = "completed"
                job.stage = "render"
                job.progress = 100
                job.completed_at = datetime.now(timezone.utc)
                db.commit()

        return {"job_id": job_id, "status": "completed"}

    except Exception as exc:
        with SessionLocal() as db:
            job = db.get(ProcessingJob, job_uuid)

            if job is not None:
                job.status = "failed"
                job.error_code = "PROCESSING_FAILED"
                job.error_message = str(exc)[:2000]
                db.commit()

        raise