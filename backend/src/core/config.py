from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[3]


def _default_storage_dir() -> Path:
    """Return the default local upload storage directory."""
    return Path(__file__).resolve().parents[2] / "storage" / "files"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env.dev",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_host: str = "backend-db"
    postgres_port: int = Field(default=5433, validation_alias="PGPORT")
    postgres_db: str = "test"
    redis_url: str = Field(
        default="redis://backend-redis:6379/0", validation_alias="REDIS_URL"
    )
    celery_broker_url_override: str | None = Field(
        default=None, validation_alias="CELERY_BROKER_URL"
    )
    celery_result_backend_override: str | None = Field(
        default=None, validation_alias="CELERY_RESULT_BACKEND"
    )
    file_processing_queue: str = Field(
        default="file-processing", validation_alias="FILE_PROCESSING_QUEUE"
    )
    process_uploaded_file_task_name: str = Field(
        default="files.process_uploaded_file",
        validation_alias="PROCESS_UPLOADED_FILE_TASK_NAME",
    )
    upload_chunk_size_bytes: int = Field(
        default=1024 * 1024, validation_alias="UPLOAD_CHUNK_SIZE_BYTES"
    )
    max_safe_file_size_bytes: int = Field(
        default=10 * 1024 * 1024, validation_alias="MAX_SAFE_FILE_SIZE_BYTES"
    )
    suspicious_file_extensions: frozenset[str] = Field(
        default=frozenset({".exe", ".bat", ".cmd", ".sh", ".js"}),
        validation_alias="SUSPICIOUS_FILE_EXTENSIONS",
    )
    storage_dir: Path = Field(default_factory=_default_storage_dir)

    @computed_field
    @property
    def database_url(self) -> str:
        """Build the async SQLAlchemy database URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field
    @property
    def celery_broker_url(self) -> str:
        """Return the Celery broker URL."""
        return self.celery_broker_url_override or self.redis_url

    @computed_field
    @property
    def celery_result_backend(self) -> str:
        """Return the Celery result backend URL."""
        return self.celery_result_backend_override or self.redis_url


settings = Settings()
