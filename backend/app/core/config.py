"""Application configuration and settings."""

from enum import Enum
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageType(str, Enum):
    """Storage backend type."""

    LOCAL = "local"
    S3 = "s3"


class DatabaseType(str, Enum):
    """Database backend type."""

    MEMORY = "memory"
    SQLITE = "sqlite"
    POSTGRES = "postgres"


class LogLevel(str, Enum):
    """Application log level."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class AssemblyTone(str, Enum):
    """Tone for assembly instructions (Phase 3)."""

    IKEA = "ikea"  # Cheerful, friendly, accessible
    TECHNICAL = "technical"  # Formal, precise, specification-focused
    BEGINNER = "beginner"  # Extra detail, safety warnings, simplification


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    # Server
    debug: bool = False
    log_level: LogLevel = LogLevel.INFO
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_type: DatabaseType = DatabaseType.MEMORY  # memory | sqlite | postgres
    database_url: str = (
        ""  # For sqlite: "sqlite:///weble.db" or postgres: "postgresql+asyncpg://user:pass@host/db"
    )
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

    # Timeouts (seconds)
    step_processing_timeout_seconds: int = 300  # 5 minutes for STEP parsing
    svg_generation_timeout_seconds: int = 60
    assembly_generation_timeout_seconds: int = 120

    # LLM
    llm_timeout_seconds: int = 30
    llm_model: str = "google/gemini-pro"
    llm_max_tokens: int = 2000

    # Phase 3: Assembly Instructions
    assembly_llm_enabled: bool = True
    assembly_tone: AssemblyTone = AssemblyTone.IKEA
    assembly_llm_model: str = "google/gemini-2.0-flash"  # Faster/cheaper variant

    # SSE (Server-Sent Events)
    sse_heartbeat_seconds: int = 2  # Progress update interval
    job_retention_hours: int = 24  # Auto-cleanup old jobs

    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
