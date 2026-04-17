"""Tests for database repository abstraction layer."""

import pytest
from app.db.repositories import BaseRepository
from app.db.in_memory_repository import InMemoryRepository
from app.db.factory import create_repository, DatabaseType
from app.models.schemas import (
    Geometry3D,
    Part,
    PartType,
    ProcessingStatus,
    SvgDrawing,
    AssemblyStep,
)


@pytest.fixture
async def in_memory_repo() -> InMemoryRepository:
    """Create an in-memory repository for testing."""
    repo = InMemoryRepository()
    yield repo
    await repo.clear_all()


class TestInMemoryRepository:
    """Test InMemoryRepository implementation."""

    @pytest.mark.asyncio
    async def test_create_and_get_job(self, in_memory_repo: InMemoryRepository):
        """Test creating and retrieving a job."""
        job_id = "job-123"
        model_id = "model-456"

        job = await in_memory_repo.create_job(job_id, model_id)
        assert job.id == job_id
        assert job.model_id == model_id
        assert job.status == ProcessingStatus.PENDING

        retrieved_job = await in_memory_repo.get_job(job_id)
        assert retrieved_job is not None
        assert retrieved_job.id == job_id

    @pytest.mark.asyncio
    async def test_update_job(self, in_memory_repo: InMemoryRepository):
        """Test updating job progress."""
        job_id = "job-123"
        model_id = "model-456"

        await in_memory_repo.create_job(job_id, model_id)

        # Update with progress
        updated_job = await in_memory_repo.update_job(
            job_id,
            status=ProcessingStatus.PROCESSING,
            progress_percent=50,
            current_stage="extracting_parts",
            action="Extracting parts...",
            eta_seconds=30,
        )

        assert updated_job is not None
        assert updated_job.status == ProcessingStatus.PROCESSING
        assert updated_job.progress_percent == 50
        assert updated_job.current_stage == "extracting_parts"
        assert updated_job.action == "Extracting parts..."
        assert updated_job.eta_seconds == 30

    @pytest.mark.asyncio
    async def test_create_and_get_model(self, in_memory_repo: InMemoryRepository):
        """Test creating and retrieving a model."""
        model_id = "model-123"
        file_name = "furniture.step"
        file_size = 1024 * 100  # 100 KB

        model = await in_memory_repo.create_model(model_id, file_name, file_size)
        assert model["id"] == model_id
        assert model["file_name"] == file_name
        assert model["file_size"] == file_size

        retrieved_model = await in_memory_repo.get_model(model_id)
        assert retrieved_model is not None
        assert retrieved_model["id"] == model_id

    @pytest.mark.asyncio
    async def test_save_and_get_geometry(self, in_memory_repo: InMemoryRepository):
        """Test saving and retrieving geometry."""
        model_id = "model-123"
        await in_memory_repo.create_model(model_id, "test.step", 1024)

        geometry = Geometry3D(
            vertices=[[0, 0, 0], [1, 0, 0], [0, 1, 0]],
            normals=[[0, 0, 1], [0, 0, 1], [0, 0, 1]],
            indices=[0, 1, 2],
            metadata={"solids_count": 1},
        )

        await in_memory_repo.save_geometry(model_id, geometry)
        retrieved_geometry = await in_memory_repo.get_geometry(model_id)

        assert retrieved_geometry is not None
        assert len(retrieved_geometry.vertices) == 3
        assert len(retrieved_geometry.normals) == 3
        assert retrieved_geometry.metadata["solids_count"] == 1

    @pytest.mark.asyncio
    async def test_save_and_get_parts(self, in_memory_repo: InMemoryRepository):
        """Test saving and retrieving parts."""
        model_id = "model-123"

        parts = [
            Part(
                id="A",
                original_index=0,
                part_type=PartType.PANEL,
                quantity=1,
                volume=100.0,
                dimensions={"width": 100, "height": 50, "depth": 10},
                centroid=[50, 25, 5],
                surface_area=5000.0,
                group_id="pg-1",
            ),
            Part(
                id="B",
                original_index=1,
                part_type=PartType.FASTENER,
                quantity=4,
                volume=5.0,
                dimensions={"width": 5, "height": 5, "depth": 50},
                centroid=[2.5, 2.5, 25],
                surface_area=500.0,
                group_id="pg-2",
            ),
        ]

        await in_memory_repo.save_parts(model_id, parts)
        retrieved_parts = await in_memory_repo.get_parts(model_id)

        assert len(retrieved_parts) == 2
        assert retrieved_parts[0].id == "A"
        assert retrieved_parts[1].part_type == PartType.FASTENER
        assert retrieved_parts[1].quantity == 4

    @pytest.mark.asyncio
    async def test_save_and_get_drawings(self, in_memory_repo: InMemoryRepository):
        """Test saving and retrieving SVG drawings."""
        model_id = "model-123"

        drawings = [
            SvgDrawing(
                part_id="A",
                svg_content="<svg>...</svg>",
                quantity_label="×1",
            ),
            SvgDrawing(
                part_id="B",
                svg_content="<svg>...</svg>",
                quantity_label="×4",
            ),
        ]

        await in_memory_repo.save_drawings(model_id, drawings)
        retrieved_drawings = await in_memory_repo.get_drawings(model_id)

        assert len(retrieved_drawings) == 2
        assert retrieved_drawings[0].part_id == "A"
        assert retrieved_drawings[1].quantity_label == "×4"

    @pytest.mark.asyncio
    async def test_save_and_get_steps(self, in_memory_repo: InMemoryRepository):
        """Test saving and retrieving assembly steps."""
        model_id = "model-123"

        steps = [
            AssemblyStep(
                step_number=1,
                title="Assemble frame",
                description="Connect left and right panels",
                part_indices=[0, 1],
                part_roles={0: "left_panel", 1: "right_panel"},
                context_part_indices=[],
                duration_minutes=5,
            ),
            AssemblyStep(
                step_number=2,
                title="Add fasteners",
                description="Screw panels together",
                part_indices=[2],
                part_roles={2: "screw"},
                context_part_indices=[0, 1],
                duration_minutes=3,
            ),
        ]

        await in_memory_repo.save_steps(model_id, steps)
        retrieved_steps = await in_memory_repo.get_steps(model_id)

        assert len(retrieved_steps) == 2
        assert retrieved_steps[0].step_number == 1
        assert len(retrieved_steps[1].context_part_indices) == 2

    @pytest.mark.asyncio
    async def test_delete_model(self, in_memory_repo: InMemoryRepository):
        """Test deleting a model and related data."""
        model_id = "model-123"
        await in_memory_repo.create_model(model_id, "test.step", 1024)

        # Add some data
        parts = [
            Part(
                id="A",
                original_index=0,
                part_type=PartType.PANEL,
                quantity=1,
                volume=100.0,
                dimensions={"width": 100},
                centroid=[50, 25, 5],
                surface_area=5000.0,
                group_id="pg-1",
            )
        ]
        await in_memory_repo.save_parts(model_id, parts)

        # Delete model
        result = await in_memory_repo.delete_model(model_id)
        assert result is True

        # Verify model is gone
        model = await in_memory_repo.get_model(model_id)
        assert model is None

        # Verify parts are gone
        parts_list = await in_memory_repo.get_parts(model_id)
        assert len(parts_list) == 0

    @pytest.mark.asyncio
    async def test_list_jobs(self, in_memory_repo: InMemoryRepository):
        """Test listing jobs."""
        # Create multiple jobs
        for i in range(5):
            await in_memory_repo.create_job(f"job-{i}", f"model-{i}")

        jobs = await in_memory_repo.list_jobs(limit=10)
        assert len(jobs) == 5

    @pytest.mark.asyncio
    async def test_health_check(self, in_memory_repo: InMemoryRepository):
        """Test health check."""
        is_healthy = await in_memory_repo.health_check()
        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_clear_all(self, in_memory_repo: InMemoryRepository):
        """Test clearing all data."""
        # Create some data
        await in_memory_repo.create_model("model-1", "test.step", 1024)
        await in_memory_repo.create_job("job-1", "model-1")

        # Clear all
        await in_memory_repo.clear_all()

        # Verify everything is gone
        assert await in_memory_repo.get_model("model-1") is None
        assert await in_memory_repo.get_job("job-1") is None


class TestRepositoryFactory:
    """Test repository factory."""

    @pytest.mark.asyncio
    async def test_create_memory_repository(self):
        """Test creating in-memory repository."""
        repo = await create_repository(db_type="memory")
        assert isinstance(repo, InMemoryRepository)
        assert await repo.health_check() is True

    @pytest.mark.asyncio
    async def test_create_sqlite_repository_requires_url(self):
        """Test that SQLite repository requires database URL."""
        with pytest.raises(ValueError):
            await create_repository(db_type="sqlite")

    @pytest.mark.asyncio
    async def test_create_postgres_repository_requires_url(self):
        """Test that PostgreSQL repository requires database URL."""
        with pytest.raises(ValueError):
            await create_repository(db_type="postgres")

    @pytest.mark.asyncio
    async def test_invalid_database_type(self):
        """Test invalid database type."""
        with pytest.raises(ValueError):
            await create_repository(db_type="invalid")
