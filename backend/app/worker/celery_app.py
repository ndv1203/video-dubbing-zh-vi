from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "video_dubbing",
    broker=settings.redis_url,
    backend="redis://redis:6379/1",
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
