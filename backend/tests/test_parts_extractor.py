"""Tests for Stage 2: Parts Extractor Service."""

import pytest
import pytest_asyncio
from app.services.parts_extractor import PartsExtractorService
from app.models.schemas import Geometry3D, Part, PartType


@pytest_asyncio.fixture
async def parts_extractor():
    """Create a PartsExtractorService instance."""
    return PartsExtractorService()


@pytest.fixture
def sample_geometry():
    """Create sample Geometry3D for testing."""
    return Geometry3D(
        vertices=[[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]],
        normals=[[0, 0, 1], [0, 0, 1], [0, 0, 1], [0, 0, 1]],
        indices=[0, 1, 2, 0, 2, 3],
        metadata={"solids_count": 1},
    )


class TestPartsExtractorValidation:
    """Test input validation for PartsExtractorService."""

    @pytest.mark.asyncio
    async def test_validate_valid_geometry(self, parts_extractor, sample_geometry):
        """Test validation of valid geometry."""
        result = await parts_extractor.validate_input(sample_geometry)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_empty_geometry(self, parts_extractor):
        """Test validation fails for empty geometry."""
        empty_geometry = Geometry3D(vertices=[], normals=[], indices=[])
        result = await parts_extractor.validate_input(empty_geometry)
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_invalid_input_type(self, parts_extractor):
        """Test validation fails for invalid input types."""
        result = await parts_extractor.validate_input("not geometry")
        assert result is False


class TestPartsExtractorProcessing:
    """Test processing logic for PartsExtractorService."""

    @pytest.mark.asyncio
    async def test_process_geometry_returns_parts(self, parts_extractor, sample_geometry):
        """Test processing geometry returns a list of Parts."""
        result = await parts_extractor.process(sample_geometry)
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(part, Part) for part in result)

    @pytest.mark.asyncio
    async def test_process_returns_classified_parts(self, parts_extractor, sample_geometry):
        """Test that returned parts have classification."""
        result = await parts_extractor.process(sample_geometry)
        for part in result:
            assert part.part_type in [
                PartType.PANEL,
                PartType.HARDWARE,
                PartType.FASTENER,
                PartType.STRUCTURAL,
                PartType.OTHER,
            ]
            assert isinstance(part.quantity, int)
            assert part.quantity > 0

    @pytest.mark.asyncio
    async def test_process_returns_part_with_id(self, parts_extractor, sample_geometry):
        """Test that returned parts have IDs."""
        result = await parts_extractor.process(sample_geometry)
        for part in result:
            assert part.id is not None
            assert len(part.id) > 0

    @pytest.mark.asyncio
    async def test_process_returns_mock_two_parts(self, parts_extractor, sample_geometry):
        """Test that mock implementation returns exactly 2 parts."""
        result = await parts_extractor.process(sample_geometry)
        assert len(result) == 2

        # Verify first part
        assert result[0].id == "A"
        assert result[0].part_type == PartType.PANEL
        assert result[0].quantity == 1

        # Verify second part
        assert result[1].id == "B"
        assert result[1].part_type == PartType.HARDWARE
        assert result[1].quantity == 4

    @pytest.mark.asyncio
    async def test_process_invalid_input_raises_error(self, parts_extractor):
        """Test processing invalid input raises ValueError."""
        with pytest.raises(ValueError):
            await parts_extractor.process(Geometry3D(vertices=[], normals=[], indices=[]))


class TestPartsExtractorMetrics:
    """Test part metrics and properties."""

    @pytest.mark.asyncio
    async def test_parts_have_volume(self, parts_extractor, sample_geometry):
        """Test that parts have volume property."""
        result = await parts_extractor.process(sample_geometry)
        for part in result:
            assert isinstance(part.volume, (int, float))
            assert part.volume > 0

    @pytest.mark.asyncio
    async def test_parts_have_dimensions(self, parts_extractor, sample_geometry):
        """Test that parts have dimensions."""
        result = await parts_extractor.process(sample_geometry)
        for part in result:
            assert isinstance(part.dimensions, dict)
            assert len(part.dimensions) > 0

    @pytest.mark.asyncio
    async def test_parts_have_centroid(self, parts_extractor, sample_geometry):
        """Test that parts have centroid coordinates."""
        result = await parts_extractor.process(sample_geometry)
        for part in result:
            assert isinstance(part.centroid, list)
            assert len(part.centroid) == 3  # x, y, z

    @pytest.mark.asyncio
    async def test_parts_have_group_id(self, parts_extractor, sample_geometry):
        """Test that parts have group ID for deduplication."""
        result = await parts_extractor.process(sample_geometry)
        for part in result:
            assert part.group_id is not None
