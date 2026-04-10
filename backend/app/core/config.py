"""Application configuration and settings."""

from enum import Enum
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageType(str, Enum):
    """Storage backend type."""

    LOCAL = "local"
    S3 = "s3"


class LogLevel(str, Enum):
    """Application log level."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    # Server
    debug: bool = False
    log_level: LogLevel = LogLevel.INFO
    host: str = "0.0.0.0"
    port: int = 8000

    # Database (will be used later when we switch from in-memory)
    database_url: str = "postgresql://user:password@localhost:5432/weble"
    database_pool_size: int = 10

    # File Storage
    storage_type: StorageType = StorageType.LOCAL
    local_storage_path: str = "./storage"

    # S3 (optional, for later)
    s3_bucket: str = ""
    s3_endpoint: str = ""
    s3_region: str = "us-east-1"
    s3_access_key: str = ""
    s3_secret_key: str = ""

    # API Keys
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Processing limits
    max_file_size_mb: int = 50
    max_parts_per_model: int = 500

    # LLM
    llm_timeout_seconds: int = 30
    llm_model: str = "google/gemini-pro"

    # SSE
    sse_heartbeat_seconds: int = 5

    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
