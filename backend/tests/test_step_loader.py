"""Tests for Stage 1: STEP Loader Service."""

import pytest
import pytest_asyncio
from app.services.step_loader import StepLoaderService
from app.core.exceptions import InvalidStepFileError, NoSolidsFoundError
from app.models.schemas import Geometry3D


@pytest_asyncio.fixture
async def step_loader():
    """Create a StepLoaderService instance."""
    return StepLoaderService()


class TestStepLoaderValidation:
    """Test input validation for StepLoaderService."""

    @pytest.mark.asyncio
    async def test_validate_valid_step_file(self, step_loader, valid_step_file_content):
        """Test validation of a valid STEP file."""
        result = await step_loader.validate_input(valid_step_file_content)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_invalid_file_not_bytes(self, step_loader):
        """Test validation fails for non-bytes input."""
        result = await step_loader.validate_input("not bytes")
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_invalid_file_signature(self, step_loader, invalid_step_file_content):
        """Test validation fails for invalid file signature."""
        result = await step_loader.validate_input(invalid_step_file_content)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_file_too_small(self, step_loader, too_small_file_content):
        """Test validation fails for files that are too small."""
        result = await step_loader.validate_input(too_small_file_content)
        assert result is False


class TestStepLoaderProcessing:
    """Test processing logic for StepLoaderService."""

    @pytest.mark.asyncio
    async def test_process_valid_step_file(self, step_loader, valid_step_file_content):
        """Test processing a valid STEP file returns Geometry3D."""
        result = await step_loader.process(valid_step_file_content)
        assert isinstance(result, Geometry3D)
        assert len(result.vertices) > 0
        assert len(result.normals) > 0
        assert len(result.indices) > 0
        assert "solids_count" in result.metadata

    @pytest.mark.asyncio
    async def test_process_invalid_step_file_raises_error(
        self, step_loader, invalid_step_file_content
    ):
        """Test processing invalid STEP file raises InvalidStepFileError."""
        with pytest.raises(InvalidStepFileError):
            await step_loader.process(invalid_step_file_content)

    @pytest.mark.asyncio
    async def test_process_returns_consistent_geometry(self, step_loader, valid_step_file_content):
        """Test that geometry returned is consistent (cube structure)."""
        result = await step_loader.process(valid_step_file_content)

        # Mock returns a cube with 8 vertices
        assert len(result.vertices) == 8

        # Mock returns a cube with 12 triangles (36 indices)
        assert len(result.indices) == 36

        # Verify geometry bounds
        assert result.metadata["solids_count"] == 1
        assert result.metadata["total_triangles"] == 12

    @pytest.mark.asyncio
    async def test_process_empty_input_raises_error(self, step_loader):
        """Test processing empty input raises InvalidStepFileError."""
        with pytest.raises(InvalidStepFileError):
            await step_loader.process(b"")


class TestStepLoaderMetadata:
    """Test metadata extraction from StepLoaderService."""

    @pytest.mark.asyncio
    async def test_geometry_has_bounds(self, step_loader, valid_step_file_content):
        """Test that returned geometry has bounds metadata."""
        result = await step_loader.process(valid_step_file_content)
        assert "bounds" in result.metadata
        assert "min" in result.metadata["bounds"]
        assert "max" in result.metadata["bounds"]

    @pytest.mark.asyncio
    async def test_geometry_has_vertex_normals(self, step_loader, valid_step_file_content):
        """Test that returned geometry has matching vertex-normal pairs."""
        result = await step_loader.process(valid_step_file_content)
        assert len(result.vertices) == len(result.normals)
