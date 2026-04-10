"""Tests for Stage 3: SVG Generator Service."""

import pytest
import pytest_asyncio
from app.services.svg_generator import SvgGeneratorService
from app.models.schemas import Part, PartType, SvgDrawing


@pytest_asyncio.fixture
async def svg_generator():
    """Create a SvgGeneratorService instance."""
    return SvgGeneratorService()


@pytest.fixture
def sample_parts():
    """Create sample parts for testing."""
    return [
        Part(
            id="A",
            original_index=0,
            part_type=PartType.PANEL,
            quantity=1,
            volume=100.5,
            dimensions={"width": 50, "height": 30, "depth": 2},
            centroid=[25, 15, 1],
            surface_area=3200,
            group_id="A",
            metrics={},
        ),
        Part(
            id="B",
            original_index=1,
            part_type=PartType.HARDWARE,
            quantity=4,
            volume=2.5,
            dimensions={"width": 5, "height": 5, "depth": 10},
            centroid=[2.5, 2.5, 5],
            surface_area=250,
            group_id="B",
            metrics={},
        ),
    ]


class TestSvgGeneratorValidation:
    """Test input validation for SvgGeneratorService."""

    @pytest.mark.asyncio
    async def test_validate_valid_parts(self, svg_generator, sample_parts):
        """Test validation of valid parts list."""
        result = await svg_generator.validate_input(sample_parts)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_empty_parts_list(self, svg_generator):
        """Test validation fails for empty parts list."""
        result = await svg_generator.validate_input([])
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_invalid_input_type(self, svg_generator):
        """Test validation fails for invalid input types."""
        result = await svg_generator.validate_input("not a list")
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_none_input(self, svg_generator):
        """Test validation fails for None input."""
        result = await svg_generator.validate_input(None)
        assert result is False


class TestSvgGeneratorProcessing:
    """Test processing logic for SvgGeneratorService."""

    @pytest.mark.asyncio
    async def test_process_parts_returns_drawings(self, svg_generator, sample_parts):
        """Test processing parts returns a list of SvgDrawing objects."""
        result = await svg_generator.process(sample_parts)
        assert isinstance(result, list)
        assert len(result) == len(sample_parts)
        assert all(isinstance(drawing, SvgDrawing) for drawing in result)

    @pytest.mark.asyncio
    async def test_process_returns_svg_content(self, svg_generator, sample_parts):
        """Test that drawings contain valid SVG content."""
        result = await svg_generator.process(sample_parts)
        for drawing in result:
            assert isinstance(drawing.svg_content, str)
            assert "<svg" in drawing.svg_content
            assert "</svg>" in drawing.svg_content

    @pytest.mark.asyncio
    async def test_process_drawing_has_part_id(self, svg_generator, sample_parts):
        """Test that drawings are labeled with part IDs."""
        result = await svg_generator.process(sample_parts)
        for i, drawing in enumerate(result):
            assert drawing.part_id == sample_parts[i].id

    @pytest.mark.asyncio
    async def test_process_empty_parts_raises_error(self, svg_generator):
        """Test processing empty parts list raises ValueError."""
        with pytest.raises(ValueError):
            await svg_generator.process([])

    @pytest.mark.asyncio
    async def test_process_svg_contains_part_label(self, svg_generator, sample_parts):
        """Test that SVG content includes part label."""
        result = await svg_generator.process(sample_parts)
        for drawing in result:
            assert f"Part {drawing.part_id}" in drawing.svg_content

    @pytest.mark.asyncio
    async def test_process_svg_contains_volume(self, svg_generator, sample_parts):
        """Test that SVG content includes volume information."""
        result = await svg_generator.process(sample_parts)
        for drawing in result:
            assert "Volume:" in drawing.svg_content


class TestSvgGeneratorQuantityLabel:
    """Test quantity label generation."""

    @pytest.mark.asyncio
    async def test_quantity_label_for_single_part(self, svg_generator, sample_parts):
        """Test that single parts don't have quantity label."""
        result = await svg_generator.process(sample_parts)
        # Part A has quantity 1
        assert "×" not in result[0].quantity_label

    @pytest.mark.asyncio
    async def test_quantity_label_for_multiple_parts(self, svg_generator, sample_parts):
        """Test that multiple parts have quantity label."""
        result = await svg_generator.process(sample_parts)
        # Part B has quantity 4
        assert "×4" in result[1].quantity_label
        assert result[1].quantity_label == "×4"

    @pytest.mark.asyncio
    async def test_svg_content_includes_quantity_for_multiples(self, svg_generator, sample_parts):
        """Test that SVG content includes quantity indicator for multiple parts."""
        result = await svg_generator.process(sample_parts)
        # Part B should have quantity indicator
        assert "×4" in result[1].svg_content
