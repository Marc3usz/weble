"""Dependency injection container for services."""

from typing import Optional
import logging

from app.core.config import Settings, settings
from app.db.repositories import BaseRepository
from app.db.factory import get_repository, reset_repository
from app.services.progress_tracker import ProgressTracker, get_progress_tracker


class ServiceContainer:
    """
    Manages all service dependencies.
    Single source of truth for all service instances.
    """

    def __init__(self, config: Settings = settings) -> None:
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize repository (abstract database interface)
        self._repository: Optional[BaseRepository] = None

        # Initialize progress tracker
        self._progress_tracker: Optional[ProgressTracker] = None

    async def initialize(self) -> None:
        """Initialize all services (call on app startup)."""
        self._repository = await get_repository()
        self._progress_tracker = await get_progress_tracker()
        self.logger.info("ServiceContainer initialized")

    async def get_repository(self) -> BaseRepository:
        """Get repository instance."""
        if self._repository is None:
            self._repository = await get_repository()
        return self._repository

    async def get_progress_tracker(self) -> ProgressTracker:
        """Get progress tracker instance."""
        if self._progress_tracker is None:
            self._progress_tracker = await get_progress_tracker()
        return self._progress_tracker

    # Keep old _db property for backward compatibility during migration
    @property
    async def _db(self) -> BaseRepository:
        """Deprecated: Use get_repository() instead."""
        return await self.get_repository()


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
    await reset_repository()
    _container = None
