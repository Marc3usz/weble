"""Tests for Phase 3: Assembly Generator with LLM Integration."""

import pytest
import pytest_asyncio

from app.services.assembly_generator import AssemblyGeneratorService
from app.services.llm_assembly_generator import LLMAssemblyGeneratorService
from app.models.schemas import Part, PartType, SvgDrawing, AssemblyStep
from app.core.config import AssemblyTone


# ============================================================================
# FIXTURES
# ============================================================================


@pytest_asyncio.fixture
async def llm_service():
    """Create LLM service."""
    service = LLMAssemblyGeneratorService()
    service.api_key = "test-api-key"  # Set test API key to avoid "not configured" error
    return service


@pytest_asyncio.fixture
async def assembly_generator(llm_service):
    """Create AssemblyGeneratorService with LLM support."""
    return AssemblyGeneratorService(llm_service=llm_service)


@pytest_asyncio.fixture
async def assembly_generator_no_llm():
    """Create AssemblyGeneratorService without LLM (rules-based only)."""
    return AssemblyGeneratorService(llm_service=None)


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
        ),
        Part(
            id="B",
            original_index=1,
            part_type=PartType.FASTENER,
            quantity=8,
            volume=1.0,
            dimensions={"width": 3, "height": 3, "depth": 10},
            centroid=[1.5, 1.5, 5],
            surface_area=120,
            group_id="B",
        ),
        Part(
            id="C",
            original_index=2,
            part_type=PartType.STRUCTURAL,
            quantity=2,
            volume=50.0,
            dimensions={"width": 20, "height": 20, "depth": 5},
            centroid=[10, 10, 2.5],
            surface_area=1400,
            group_id="C",
        ),
    ]


@pytest.fixture
def sample_drawings(sample_parts):
    """Create sample SVG drawings."""
    return [
        SvgDrawing(part_id=part.id, svg_content=f"<svg>Part {part.id}</svg>")
        for part in sample_parts
    ]


@pytest.fixture
def furniture_parts():
    """Create a furniture-like panel set to validate assembly semantics."""
    return [
        Part(
            id="BASE",
            original_index=0,
            part_type=PartType.PANEL,
            quantity=1,
            volume=5760000,
            dimensions={"width": 800, "height": 400, "depth": 18},
            centroid=[0, 0, 0],
            surface_area=0,
            group_id="BASE",
        ),
        Part(
            id="LEFT",
            original_index=1,
            part_type=PartType.PANEL,
            quantity=1,
            volume=5184000,
            dimensions={"width": 720, "height": 400, "depth": 18},
            centroid=[0, 0, 0],
            surface_area=0,
            group_id="LEFT",
        ),
        Part(
            id="RIGHT",
            original_index=2,
            part_type=PartType.PANEL,
            quantity=1,
            volume=5184000,
            dimensions={"width": 720, "height": 400, "depth": 18},
            centroid=[0, 0, 0],
            surface_area=0,
            group_id="RIGHT",
        ),
        Part(
            id="TOP",
            original_index=3,
            part_type=PartType.PANEL,
            quantity=1,
            volume=5760000,
            dimensions={"width": 800, "height": 400, "depth": 18},
            centroid=[0, 0, 0],
            surface_area=0,
            group_id="TOP",
        ),
        Part(
            id="BACK",
            original_index=4,
            part_type=PartType.PANEL,
            quantity=1,
            volume=1638000,
            dimensions={"width": 780, "height": 700, "depth": 3},
            centroid=[0, 0, 0],
            surface_area=0,
            group_id="BACK",
        ),
        Part(
            id="SCREWS",
            original_index=5,
            part_type=PartType.FASTENER,
            quantity=12,
            volume=120,
            dimensions={"width": 4, "height": 4, "depth": 40},
            centroid=[0, 0, 0],
            surface_area=0,
            group_id="SCREWS",
        ),
    ]


@pytest.fixture
def furniture_drawings(furniture_parts):
    return [
        SvgDrawing(part_id=part.id, svg_content=f"<svg>{part.id}</svg>") for part in furniture_parts
    ]


# ============================================================================
# RULES-BASED TESTS (Always work, no API dependency)
# ============================================================================


class TestAssemblyGeneratorRulesBased:
    """Test assembly generation with rules-based approach (no LLM)."""

    @pytest.mark.asyncio
    async def test_rules_based_generation_works(
        self, assembly_generator_no_llm, sample_parts, sample_drawings
    ):
        """Test that rules-based generation produces valid steps."""
        result = await assembly_generator_no_llm.process(sample_parts, sample_drawings)
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(step, AssemblyStep) for step in result)

    @pytest.mark.asyncio
    async def test_rules_based_ikea_tone(
        self, assembly_generator_no_llm, sample_parts, sample_drawings
    ):
        """Test IKEA tone rules-based generation."""
        result = await assembly_generator_no_llm.process(
            sample_parts, sample_drawings, tone=AssemblyTone.IKEA
        )
        assert len(result) > 0
        assert all(isinstance(step, AssemblyStep) for step in result)

    @pytest.mark.asyncio
    async def test_rules_based_ikea_tone_stays_technical_and_plain(
        self, assembly_generator_no_llm, sample_parts, sample_drawings
    ):
        """Even friendly tone should avoid fluff in assembly copy."""
        result = await assembly_generator_no_llm.process(
            sample_parts, sample_drawings, tone=AssemblyTone.IKEA
        )

        assert result
        combined_text = " ".join(
            filter(
                None,
                [
                    step.title + " " + step.description + " " + step.detail_description
                    for step in result
                ],
            )
        ).lower()
        assert "fun part" not in combined_text
        assert "enjoy the process" not in combined_text
        assert "super easy" not in combined_text
        assert "👍" not in combined_text

    @pytest.mark.asyncio
    async def test_rules_based_technical_tone(
        self, assembly_generator_no_llm, sample_parts, sample_drawings
    ):
        """Test TECHNICAL tone rules-based generation."""
        result = await assembly_generator_no_llm.process(
            sample_parts, sample_drawings, tone=AssemblyTone.TECHNICAL
        )
        assert len(result) > 0
        assert all(isinstance(step, AssemblyStep) for step in result)

    @pytest.mark.asyncio
    async def test_rules_based_beginner_tone(
        self, assembly_generator_no_llm, sample_parts, sample_drawings
    ):
        """Test BEGINNER tone rules-based generation."""
        result = await assembly_generator_no_llm.process(
            sample_parts, sample_drawings, tone=AssemblyTone.BEGINNER
        )
        assert len(result) > 0
        assert all(isinstance(step, AssemblyStep) for step in result)
        assert any(step.warnings or step.tips for step in result)

    @pytest.mark.asyncio
    async def test_rules_based_has_phase3_fields(
        self, assembly_generator_no_llm, sample_parts, sample_drawings
    ):
        """Test that rules-based steps include Phase 3 fields."""
        result = await assembly_generator_no_llm.process(sample_parts, sample_drawings)
        assert any(step.detail_description for step in result)
        assert any(step.warnings or step.tips for step in result)

    @pytest.mark.asyncio
    async def test_rules_based_steps_not_llm_generated(
        self, assembly_generator_no_llm, sample_parts, sample_drawings
    ):
        """Test that rules-based steps are marked as not LLM-generated."""
        result = await assembly_generator_no_llm.process(sample_parts, sample_drawings)
        assert all(not step.is_llm_generated for step in result)

    @pytest.mark.asyncio
    async def test_rules_based_furniture_flow_uses_semantic_panel_roles(
        self, assembly_generator_no_llm, furniture_parts, furniture_drawings
    ):
        """Furniture-like models should start with a meaningful frame sequence."""
        result = await assembly_generator_no_llm.process(
            furniture_parts, furniture_drawings, tone=AssemblyTone.TECHNICAL
        )

        assert len(result) >= 3

        first_roles = " ".join(result[0].part_roles.values()).lower()
        assert "base panel" in first_roles
        assert "side panel" in first_roles

        back_panel_steps = [
            step for step in result if "back panel" in " ".join(step.part_roles.values()).lower()
        ]
        assert back_panel_steps
        assert back_panel_steps[0].step_number > result[0].step_number


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


class TestEdgeCases:
    """Test edge cases for assembly generation with Phase 3."""

    @pytest.mark.asyncio
    async def test_single_part_assembly(self, assembly_generator_no_llm):
        """Test assembly with single part."""
        single_part = [
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
            )
        ]
        single_drawing = [SvgDrawing(part_id="A", svg_content="<svg>Part A</svg>")]
        result = await assembly_generator_no_llm.process(single_part, single_drawing)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_many_identical_parts(self, assembly_generator_no_llm):
        """Test assembly with many identical parts."""
        many_parts = [
            Part(
                id="A",
                original_index=0,
                part_type=PartType.FASTENER,
                quantity=16,
                volume=1.0,
                dimensions={"width": 3, "height": 3, "depth": 10},
                centroid=[1.5, 1.5, 5],
                surface_area=120,
                group_id="A",
            )
        ]
        many_drawing = [SvgDrawing(part_id="A", svg_content="<svg>Part A</svg>")]
        result = await assembly_generator_no_llm.process(many_parts, many_drawing)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_preview_mode_still_works(
        self, assembly_generator_no_llm, sample_parts, sample_drawings
    ):
        """Test that preview mode still works with Phase 3 services."""
        result = await assembly_generator_no_llm.process(
            sample_parts, sample_drawings, preview_only=True
        )
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_preview_mode_returns_steps(
        self, assembly_generator_no_llm, sample_parts, sample_drawings
    ):
        """Test that preview mode returns valid assembly steps."""
        result = await assembly_generator_no_llm.process(
            sample_parts, sample_drawings, preview_only=True
        )
        assert all(isinstance(step, AssemblyStep) for step in result)
        assert all(step.title for step in result)
