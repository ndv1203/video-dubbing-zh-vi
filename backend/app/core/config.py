from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"
    storage_root: str = "/data/storage"
    models_root: str = "/data/models"
    max_upload_size_mb: int = 500
    max_video_duration_seconds: int = 600
    app_env: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
