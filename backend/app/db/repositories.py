"""Abstract repository interface for database abstraction (Repository Pattern)."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from app.models.schemas import (
    AssemblyStep,
    Geometry3D,
    Part,
    ProcessingJob,
    ProcessingStatus,
    SvgDrawing,
)


class BaseRepository(ABC):
    """
    Abstract base repository defining the interface for all database operations.

    Supports Bridge Pattern for swapping implementations:
    - InMemoryRepository (development)
    - SQLiteRepository (testing)
    - PostgresRepository (production)
    """

    # ========== Job Management ==========

    @abstractmethod
    async def create_job(
        self, job_id: str, model_id: str, status: ProcessingStatus = ProcessingStatus.PENDING
    ) -> ProcessingJob:
        """Create a new processing job."""
        pass

    @abstractmethod
    async def get_job(self, job_id: str) -> Optional[ProcessingJob]:
        """Get job by ID."""
        pass

    @abstractmethod
    async def update_job(
        self,
        job_id: str,
        status: Optional[ProcessingStatus] = None,
        progress_percent: Optional[int] = None,
        current_stage: Optional[str] = None,
        error_message: Optional[str] = None,
        action: Optional[str] = None,
        eta_seconds: Optional[int] = None,
    ) -> Optional[ProcessingJob]:
        """Update job status and progress."""
        pass

    @abstractmethod
    async def list_jobs(self, limit: int = 100) -> List[ProcessingJob]:
        """List recent jobs."""
        pass

    @abstractmethod
    async def delete_job(self, job_id: str) -> bool:
        """Delete a job (for cleanup)."""
        pass

    # ========== Model Management ==========

    @abstractmethod
    async def create_model(self, model_id: str, file_name: str, file_size: int) -> Dict:
        """Create a new model record."""
        pass

    @abstractmethod
    async def get_model(self, model_id: str) -> Optional[Dict]:
        """Get model by ID."""
        pass

    @abstractmethod
    async def save_geometry(self, model_id: str, geometry: Geometry3D) -> None:
        """Save geometry for a model."""
        pass

    @abstractmethod
    async def get_geometry(self, model_id: str) -> Optional[Geometry3D]:
        """Get geometry for a model."""
        pass

    @abstractmethod
    async def delete_model(self, model_id: str) -> bool:
        """Delete a model and all related data."""
        pass

    # ========== Parts Management ==========

    @abstractmethod
    async def save_parts(self, model_id: str, parts: List[Part]) -> None:
        """Save parts for a model."""
        pass

    @abstractmethod
    async def get_parts(self, model_id: str) -> List[Part]:
        """Get parts for a model."""
        pass

    # ========== Drawings Management ==========

    @abstractmethod
    async def save_drawings(self, model_id: str, drawings: List[SvgDrawing]) -> None:
        """Save SVG drawings for a model."""
        pass

    @abstractmethod
    async def get_drawings(self, model_id: str) -> List[SvgDrawing]:
        """Get SVG drawings for a model."""
        pass

    # ========== Assembly Steps Management ==========

    @abstractmethod
    async def save_steps(self, model_id: str, steps: List[AssemblyStep]) -> None:
        """Save assembly steps for a model."""
        pass

    @abstractmethod
    async def get_steps(self, model_id: str) -> List[AssemblyStep]:
        """Get assembly steps for a model."""
        pass

    # ========== Utility Methods ==========

    @abstractmethod
    async def clear_all(self) -> None:
        """Clear all data (for testing)."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if database is healthy."""
        pass
