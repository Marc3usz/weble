"""Tests for Stage 4: Assembly Generator Service."""

import pytest
import pytest_asyncio
from app.services.assembly_generator import AssemblyGeneratorService
from app.models.schemas import Part, PartType, SvgDrawing, AssemblyStep


@pytest_asyncio.fixture
async def assembly_generator():
    """Create an AssemblyGeneratorService instance."""
    return AssemblyGeneratorService()


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


@pytest.fixture
def sample_drawings(sample_parts):
    """Create sample SVG drawings for testing."""
    return [
        SvgDrawing(part_id=part.id, svg_content=f"<svg>Part {part.id}</svg>")
        for part in sample_parts
    ]


class TestAssemblyGeneratorValidation:
    """Test input validation for AssemblyGeneratorService."""

    @pytest.mark.asyncio
    async def test_validate_valid_parts_and_drawings(
        self, assembly_generator, sample_parts, sample_drawings
    ):
        """Test validation of valid parts and drawings."""
        result = await assembly_generator.validate_input((sample_parts, sample_drawings))
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_empty_parts(self, assembly_generator, sample_drawings):
        """Test validation fails for empty parts list."""
        result = await assembly_generator.validate_input(([], sample_drawings))
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_empty_drawings(self, assembly_generator, sample_parts):
        """Test validation fails for empty drawings list."""
        result = await assembly_generator.validate_input((sample_parts, []))
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_invalid_input_type(self, assembly_generator):
        """Test validation fails for invalid input types."""
        result = await assembly_generator.validate_input("not a tuple")
        assert result is False


class TestAssemblyGeneratorProcessing:
    """Test processing logic for AssemblyGeneratorService."""

    @pytest.mark.asyncio
    async def test_process_returns_assembly_steps(
        self, assembly_generator, sample_parts, sample_drawings
    ):
        """Test processing parts and drawings returns assembly steps."""
        result = await assembly_generator.process(sample_parts, sample_drawings)
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(step, AssemblyStep) for step in result)

    @pytest.mark.asyncio
    async def test_process_returns_mock_two_steps(
        self, assembly_generator, sample_parts, sample_drawings
    ):
        """Test that mock implementation returns exactly 2 assembly steps."""
        result = await assembly_generator.process(sample_parts, sample_drawings)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_process_steps_have_titles(
        self, assembly_generator, sample_parts, sample_drawings
    ):
        """Test that assembly steps have titles."""
        result = await assembly_generator.process(sample_parts, sample_drawings)
        for step in result:
            assert isinstance(step.title, str)
            assert len(step.title) > 0

    @pytest.mark.asyncio
    async def test_process_steps_have_descriptions(
        self, assembly_generator, sample_parts, sample_drawings
    ):
        """Test that assembly steps have descriptions."""
        result = await assembly_generator.process(sample_parts, sample_drawings)
        for step in result:
            assert isinstance(step.description, str)
            assert len(step.description) > 0

    @pytest.mark.asyncio
    async def test_process_steps_have_step_numbers(
        self, assembly_generator, sample_parts, sample_drawings
    ):
        """Test that assembly steps have sequential step numbers."""
        result = await assembly_generator.process(sample_parts, sample_drawings)
        for i, step in enumerate(result, 1):
            assert step.step_number == i

    @pytest.mark.asyncio
    async def test_process_invalid_input_raises_error(self, assembly_generator):
        """Test processing invalid input raises ValueError."""
        with pytest.raises(ValueError):
            await assembly_generator.process([], [])


class TestAssemblyStepProperties:
    """Test assembly step properties."""

    @pytest.mark.asyncio
    async def test_steps_have_part_indices(self, assembly_generator, sample_parts, sample_drawings):
        """Test that steps indicate which parts are used."""
        result = await assembly_generator.process(sample_parts, sample_drawings)
        for step in result:
            assert isinstance(step.part_indices, list)
            assert len(step.part_indices) > 0

    @pytest.mark.asyncio
    async def test_steps_have_part_roles(self, assembly_generator, sample_parts, sample_drawings):
        """Test that steps define roles for parts."""
        result = await assembly_generator.process(sample_parts, sample_drawings)
        for step in result:
            assert isinstance(step.part_roles, dict)
            assert len(step.part_roles) > 0

    @pytest.mark.asyncio
    async def test_steps_have_duration(self, assembly_generator, sample_parts, sample_drawings):
        """Test that steps have estimated duration."""
        result = await assembly_generator.process(sample_parts, sample_drawings)
        for step in result:
            assert isinstance(step.duration_minutes, int)
            assert step.duration_minutes >= 0


class TestAssemblyGeneratorPreviewMode:
    """Test assembly generator preview mode."""

    @pytest.mark.asyncio
    async def test_process_with_preview_only_flag(
        self, assembly_generator, sample_parts, sample_drawings
    ):
        """Test that preview_only parameter is accepted."""
        result = await assembly_generator.process(sample_parts, sample_drawings, preview_only=True)
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_preview_returns_same_format(
        self, assembly_generator, sample_parts, sample_drawings
    ):
        """Test that preview mode returns same format as full mode."""
        result_preview = await assembly_generator.process(
            sample_parts, sample_drawings, preview_only=True
        )
        result_full = await assembly_generator.process(
            sample_parts, sample_drawings, preview_only=False
        )

        assert len(result_preview) == len(result_full)
        assert all(isinstance(step, AssemblyStep) for step in result_preview)
