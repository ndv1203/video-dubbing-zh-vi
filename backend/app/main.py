from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine

app = FastAPI(
    title="Video Dubbing API",
    description="Chinese-to-Vietnamese video dubbing service",
    version="0.1.0",
)


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

    return {
        "status": "ok",
        "database": "connected",
    }