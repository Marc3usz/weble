"""Dependency injection container for services."""

from typing import Optional
import logging

from app.core.config import Settings, settings
from app.db.memory import InMemoryDatabase, get_database
from app.services.progress_tracker import ProgressTracker, get_progress_tracker


class ServiceContainer:
    """
    Manages all service dependencies.
    Single source of truth for all service instances.
    """

    def __init__(self, config: Settings = settings) -> None:
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize database
        self._db: Optional[InMemoryDatabase] = None

        # Initialize progress tracker
        self._progress_tracker: Optional[ProgressTracker] = None

    async def initialize(self) -> None:
        """Initialize all services (call on app startup)."""
        self._db = await get_database()
        self._progress_tracker = await get_progress_tracker()
        self.logger.info("ServiceContainer initialized")

    @property
    async def database(self) -> InMemoryDatabase:
        """Get database instance."""
        if self._db is None:
            self._db = await get_database()
        return self._db

    @property
    async def progress_tracker(self) -> ProgressTracker:
        """Get progress tracker instance."""
        if self._progress_tracker is None:
            self._progress_tracker = await get_progress_tracker()
        return self._progress_tracker


# Global container instance
_container: Optional[ServiceContainer] = None


async def get_container() -> ServiceContainer:
    """Get or create the global container."""
    global _container
    if _container is None:
        _container = ServiceContainer(settings)
        await _container.initialize()
    return _container


async def reset_container() -> None:
    """Reset the global container (for testing)."""
    global _container
    _container = None
