from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.endpoints import jobs
from app.core.config import settings
from app.db.session import engine

app = FastAPI(
    title="Video Dubbing API",
    description="Chinese-to-Vietnamese video dubbing service",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])


@app.get("/")
def root():
    return {
        "message": "Video Dubbing API",
        "status": "running",
    }


@app.get("/api/v1/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        ) from exc

    redis_client = Redis.from_url(
        settings.redis_url,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    try:
        redis_client.ping()
    except RedisError as exc:
        raise HTTPException(
            status_code=503,
            detail="Redis unavailable",
        ) from exc
    finally:
        redis_client.close()

    return {
        "status": "ok",
        "database": "connected",
        "redis": "connected",
    }