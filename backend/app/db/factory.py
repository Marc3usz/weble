"""Repository factory for creating the appropriate database implementation."""

from enum import Enum
from typing import Optional

from app.db.repositories import BaseRepository
from app.db.in_memory_repository import InMemoryRepository


class DatabaseType(str, Enum):
    """Supported database backend types."""

    MEMORY = "memory"
    SQLITE = "sqlite"
    POSTGRES = "postgres"


async def create_repository(
    db_type: str = "memory", database_url: Optional[str] = None
) -> BaseRepository:
    """
    Create a repository instance based on the specified database type.

    Args:
        db_type: Type of database (memory, sqlite, postgres)
        database_url: Connection URL for SQLite/PostgreSQL

    Returns:
        BaseRepository: Concrete repository implementation

    Raises:
        ValueError: If db_type is invalid or required URL is missing
    """
    if db_type == DatabaseType.MEMORY or db_type == "memory":
        from app.db.in_memory_repository import get_in_memory_repository

        return await get_in_memory_repository()

    elif db_type == DatabaseType.SQLITE or db_type == "sqlite":
        if not database_url:
            raise ValueError("database_url required for SQLite backend")
        from app.db.sqlite_repository import SQLiteRepository

        return SQLiteRepository(database_url)

    elif db_type == DatabaseType.POSTGRES or db_type == "postgres":
        if not database_url:
            raise ValueError("database_url required for PostgreSQL backend")
        from app.db.postgres_repository import PostgresRepository

        return PostgresRepository(database_url)

    else:
        raise ValueError(f"Unknown database type: {db_type}. Use: memory, sqlite, postgres")


# Global repository instance
_repository: Optional[BaseRepository] = None


async def get_repository() -> BaseRepository:
    """Get the global repository instance."""
    global _repository
    if _repository is None:
        # Import here to avoid circular imports
        from app.core.config import settings

        _repository = await create_repository(
            db_type=settings.database_type,
            database_url=settings.database_url,
        )
    return _repository


async def reset_repository() -> None:
    """Reset the global repository (for testing)."""
    global _repository
    if _repository:
        await _repository.clear_all()
    _repository = None
