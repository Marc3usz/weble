"""In-memory repository implementation for development."""

from typing import Dict, List, Optional

from app.db.repositories import BaseRepository
from app.models.schemas import (
    AssemblyStep,
    Geometry3D,
    Part,
    ProcessingJob,
    ProcessingStatus,
    SvgDrawing,
)


class InMemoryRepository(BaseRepository):
    """In-memory repository implementation using dictionaries."""

    def __init__(self) -> None:
        self.models: Dict[str, Dict] = {}  # model_id -> model data
        self.jobs: Dict[str, ProcessingJob] = {}  # job_id -> job
        self.parts: Dict[str, List[Part]] = {}  # model_id -> parts
        self.drawings: Dict[str, List[SvgDrawing]] = {}  # model_id -> drawings
        self.steps: Dict[str, List[AssemblyStep]] = {}  # model_id -> steps

    # ========== Job Management ==========

    async def create_job(
        self, job_id: str, model_id: str, status: ProcessingStatus = ProcessingStatus.PENDING
    ) -> ProcessingJob:
        """Create a new processing job."""
        job = ProcessingJob(id=job_id, model_id=model_id, status=status)
        self.jobs[job_id] = job
        return job

    async def get_job(self, job_id: str) -> Optional[ProcessingJob]:
        """Get job by ID."""
        return self.jobs.get(job_id)

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
        job = self.jobs.get(job_id)
        if not job:
            return None

        if status is not None:
            job.status = status
        if progress_percent is not None:
            job.progress_percent = progress_percent
        if current_stage is not None:
            job.current_stage = current_stage
        if error_message is not None:
            job.error_message = error_message
        if action is not None:
            job.action = action
        if eta_seconds is not None:
            job.eta_seconds = eta_seconds

        return job

    async def list_jobs(self, limit: int = 100) -> List[ProcessingJob]:
        """List recent jobs."""
        return list(self.jobs.values())[-limit:]

    async def delete_job(self, job_id: str) -> bool:
        """Delete a job (for cleanup)."""
        if job_id in self.jobs:
            del self.jobs[job_id]
            return True
        return False

    # ========== Model Management ==========

    async def create_model(self, model_id: str, file_name: str, file_size: int) -> Dict:
        """Create a new model record."""
        model = {
            "id": model_id,
            "file_name": file_name,
            "file_size": file_size,
            "geometry": None,
            "metadata": {},
        }
        self.models[model_id] = model
        return model

    async def get_model(self, model_id: str) -> Optional[Dict]:
        """Get model by ID."""
        return self.models.get(model_id)

    async def save_geometry(self, model_id: str, geometry: Geometry3D) -> None:
        """Save geometry for a model."""
        if model_id in self.models:
            self.models[model_id]["geometry"] = geometry

    async def get_geometry(self, model_id: str) -> Optional[Geometry3D]:
        """Get geometry for a model."""
        model = self.models.get(model_id)
        if model:
            return model.get("geometry")
        return None

    async def delete_model(self, model_id: str) -> bool:
        """Delete a model and all related data."""
        if model_id in self.models:
            del self.models[model_id]
            self.parts.pop(model_id, None)
            self.drawings.pop(model_id, None)
            self.steps.pop(model_id, None)
            return True
        return False

    # ========== Parts Management ==========

    async def save_parts(self, model_id: str, parts: List[Part]) -> None:
        """Save parts for a model."""
        self.parts[model_id] = parts

    async def get_parts(self, model_id: str) -> List[Part]:
        """Get parts for a model."""
        return self.parts.get(model_id, [])

    # ========== Drawings Management ==========

    async def save_drawings(self, model_id: str, drawings: List[SvgDrawing]) -> None:
        """Save SVG drawings for a model."""
        self.drawings[model_id] = drawings

    async def get_drawings(self, model_id: str) -> List[SvgDrawing]:
        """Get SVG drawings for a model."""
        return self.drawings.get(model_id, [])

    # ========== Assembly Steps Management ==========

    async def save_steps(self, model_id: str, steps: List[AssemblyStep]) -> None:
        """Save assembly steps for a model."""
        self.steps[model_id] = steps

    async def get_steps(self, model_id: str) -> List[AssemblyStep]:
        """Get assembly steps for a model."""
        return self.steps.get(model_id, [])

    # ========== Utility Methods ==========

    async def clear_all(self) -> None:
        """Clear all data (for testing)."""
        self.models.clear()
        self.jobs.clear()
        self.parts.clear()
        self.drawings.clear()
        self.steps.clear()

    async def health_check(self) -> bool:
        """Check if database is healthy."""
        return True


# Global instance
_repository_instance: Optional[InMemoryRepository] = None


async def get_in_memory_repository() -> InMemoryRepository:
    """Get or create the global in-memory repository instance."""
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = InMemoryRepository()
    return _repository_instance
