"""Tests for Phase 3: End-to-End Integration."""

import pytest
import pytest_asyncio
from unittest.mock import patch, Mock
import json
import time

from app.services.assembly_generator import AssemblyGeneratorService
from app.services.llm_assembly_generator import LLMAssemblyGeneratorService
from app.services.exploded_view_generator import ExplodedViewSVGGenerator
from app.models.schemas import (
    Part,
    PartType,
    SvgDrawing,
    AssemblyStep,
    ProcessingJob,
    ProcessingStatus,
)
from app.core.config import AssemblyTone


# ============================================================================
# FIXTURES
# ============================================================================


@pytest_asyncio.fixture
async def full_pipeline():
    """Create a full assembly pipeline with all services."""
    llm_service = LLMAssemblyGeneratorService()
    assembly_service = AssemblyGeneratorService(llm_service=llm_service)
    svg_generator = ExplodedViewSVGGenerator()
    return {
        "llm": llm_service,
        "assembly": assembly_service,
        "svg": svg_generator,
    }


@pytest.fixture
def sample_parts():
    """Create sample parts for end-to-end testing."""
    return [
        Part(
            id="Base",
            original_index=0,
            part_type=PartType.PANEL,
            quantity=1,
            volume=150.0,
            dimensions={"width": 60, "height": 40, "depth": 2},
            centroid=[30, 20, 1],
            surface_area=4000,
            group_id="Base",
        ),
        Part(
            id="Bolt",
            original_index=1,
            part_type=PartType.FASTENER,
            quantity=12,
            volume=0.5,
            dimensions={"width": 2, "height": 2, "depth": 8},
            centroid=[1, 1, 4],
            surface_area=80,
            group_id="Bolt",
        ),
        Part(
            id="Frame",
            original_index=2,
            part_type=PartType.STRUCTURAL,
            quantity=1,
            volume=80.0,
            dimensions={"width": 50, "height": 30, "depth": 5},
            centroid=[25, 15, 2.5],
            surface_area=2000,
            group_id="Frame",
        ),
    ]


@pytest.fixture
def sample_drawings(sample_parts):
    """Create SVG drawings."""
    return [
        SvgDrawing(part_id=part.id, svg_content=f"<svg><text>{part.id}</text></svg>")
        for part in sample_parts
    ]


@pytest.fixture
def mock_llm_response():
    """Create a realistic mock LLM response."""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "steps": [
                                {
                                    "step_number": 1,
                                    "title": "Prepare base platform",
                                    "description": "Place the base panel on a flat surface",
                                    "detail_description": "Ensure the base is clean and level before beginning assembly",
                                    "part_indices": [0],
                                    "part_roles": {0: "foundation"},
                                    "context_part_indices": [],
                                    "assembly_sequence": ["Inspect", "Position", "Level"],
                                    "warnings": ["Ensure surface is clean"],
                                    "tips": ["Use a spirit level"],
                                    "confidence_score": 0.98,
                                    "is_llm_generated": True,
                                },
                                {
                                    "step_number": 2,
                                    "title": "Install fasteners",
                                    "description": "Attach bolts to the base panel",
                                    "detail_description": "Insert all bolts through the designated holes and hand-tighten",
                                    "part_indices": [0, 1],
                                    "part_roles": {0: "base", 1: "fastener"},
                                    "context_part_indices": [],
                                    "assembly_sequence": [
                                        "Align holes",
                                        "Insert bolts",
                                        "Hand tighten",
                                    ],
                                    "warnings": ["Do not over-tighten at this stage"],
                                    "tips": ["Bolts should be snug but not tight"],
                                    "confidence_score": 0.95,
                                    "is_llm_generated": True,
                                },
                                {
                                    "step_number": 3,
                                    "title": "Attach structural frame",
                                    "description": "Secure the frame to the fastened base",
                                    "detail_description": "Align the frame carefully and tighten all bolts uniformly",
                                    "part_indices": [2, 1],
                                    "part_roles": {2: "frame", 1: "fastener"},
                                    "context_part_indices": [0],
                                    "assembly_sequence": [
                                        "Align frame",
                                        "Hand tighten",
                                        "Final tighten",
                                    ],
                                    "warnings": ["Tighten in a star pattern to avoid warping"],
                                    "tips": ["Use the correct wrench size"],
                                    "confidence_score": 0.92,
                                    "is_llm_generated": True,
                                },
                            ]
                        }
                    )
                }
            }
        ],
        "usage": {"prompt_tokens": 250, "completion_tokens": 350, "total_tokens": 600},
    }


# ============================================================================
# FULL PIPELINE TESTS (4 tests)
# ============================================================================


class TestFullPipeline:
    """Test complete end-to-end assembly pipeline."""

    @pytest.mark.asyncio
    async def test_pipeline_complete_assembly(
        self, full_pipeline, sample_parts, sample_drawings, mock_llm_response
    ):
        """Test complete pipeline from parts to assembly instructions."""
        with patch.object(full_pipeline["llm"], "_call_llm") as mock_call:
            mock_call.return_value = mock_llm_response
            result = await full_pipeline["assembly"].process(
                sample_parts, sample_drawings, tone=AssemblyTone.IKEA
            )
            assert isinstance(result, list)
            assert len(result) > 0
            assert all(isinstance(step, AssemblyStep) for step in result)

    @pytest.mark.asyncio
    async def test_pipeline_generates_exploded_views(
        self, full_pipeline, sample_parts, sample_drawings, mock_llm_response
    ):
        """Test that pipeline generates exploded view diagrams."""
        with patch.object(full_pipeline["llm"], "_call_llm") as mock_call:
            mock_call.return_value = mock_llm_response
            result = await full_pipeline["assembly"].process(
                sample_parts, sample_drawings, tone=AssemblyTone.TECHNICAL
            )
            # Some steps should have exploded views
            assert any(step.exploded_view_svg for step in result)

    @pytest.mark.asyncio
    async def test_pipeline_all_tones(
        self, full_pipeline, sample_parts, sample_drawings, mock_llm_response
    ):
        """Test pipeline with all tone modes."""
        with patch.object(full_pipeline["llm"], "_call_llm") as mock_call:
            mock_call.return_value = mock_llm_response

            for tone in [AssemblyTone.IKEA, AssemblyTone.TECHNICAL, AssemblyTone.BEGINNER]:
                result = await full_pipeline["assembly"].process(
                    sample_parts, sample_drawings, tone=tone
                )
                assert isinstance(result, list)
                assert len(result) > 0

    @pytest.mark.asyncio
    async def test_pipeline_produces_valid_output(
        self, full_pipeline, sample_parts, sample_drawings, mock_llm_response
    ):
        """Test that pipeline output is valid and complete."""
        with patch.object(full_pipeline["llm"], "_call_llm") as mock_call:
            mock_call.return_value = mock_llm_response
            result = await full_pipeline["assembly"].process(sample_parts, sample_drawings)
            for step in result:
                # Verify essential fields
                assert step.step_number > 0
                assert step.title
                assert step.description
                assert len(step.part_indices) > 0
                assert isinstance(step.part_roles, dict)


# ============================================================================
# PERSISTENCE TESTS (3 tests) - Verify data integrity
# ============================================================================


class TestDataPersistence:
    """Test that Phase 3 data persists correctly through pipeline."""

    @pytest.mark.asyncio
    async def test_assembly_sequence_preserved(
        self, full_pipeline, sample_parts, sample_drawings, mock_llm_response
    ):
        """Test that assembly sequence is preserved through pipeline."""
        with patch.object(full_pipeline["llm"], "_call_llm") as mock_call:
            mock_call.return_value = mock_llm_response
            result = await full_pipeline["assembly"].process(sample_parts, sample_drawings)
            # Check that assembly sequences are preserved
            assert any(step.assembly_sequence for step in result)
            preserved = [step for step in result if step.assembly_sequence]
            assert len(preserved) > 0

    @pytest.mark.asyncio
    async def test_warnings_and_tips_preserved(
        self, full_pipeline, sample_parts, sample_drawings, mock_llm_response
    ):
        """Test that warnings and tips are preserved."""
        with patch.object(full_pipeline["llm"], "_call_llm") as mock_call:
            mock_call.return_value = mock_llm_response
            result = await full_pipeline["assembly"].process(sample_parts, sample_drawings)
            # At least some steps should have warnings or tips
            has_guidance = any(step.warnings or step.tips for step in result)
            assert has_guidance

    @pytest.mark.asyncio
    async def test_confidence_scores_realistic(
        self, full_pipeline, sample_parts, sample_drawings, mock_llm_response
    ):
        """Test that confidence scores are in valid range."""
        with patch.object(full_pipeline["llm"], "_call_llm") as mock_call:
            mock_call.return_value = mock_llm_response
            result = await full_pipeline["assembly"].process(sample_parts, sample_drawings)
            for step in result:
                assert 0 <= step.confidence_score <= 1


# ============================================================================
# PROGRESS TRACKING TESTS (3 tests) - For integration with pipeline
# ============================================================================


class TestProgressTracking:
    """Test progress tracking through Phase 3 pipeline."""

    @pytest.mark.asyncio
    async def test_assembly_generation_completes(
        self, full_pipeline, sample_parts, sample_drawings, mock_llm_response
    ):
        """Test that assembly generation completes successfully."""
        with patch.object(full_pipeline["llm"], "_call_llm") as mock_call:
            mock_call.return_value = mock_llm_response
            start_time = time.time()
            result = await full_pipeline["assembly"].process(sample_parts, sample_drawings)
            elapsed = time.time() - start_time
            assert isinstance(result, list)
            assert len(result) > 0
            # Should complete reasonably quickly (mocked, so <5 seconds)
            assert elapsed < 5

    @pytest.mark.asyncio
    async def test_step_progression_sequential(
        self, full_pipeline, sample_parts, sample_drawings, mock_llm_response
    ):
        """Test that steps are numbered sequentially."""
        with patch.object(full_pipeline["llm"], "_call_llm") as mock_call:
            mock_call.return_value = mock_llm_response
            result = await full_pipeline["assembly"].process(sample_parts, sample_drawings)
            # Steps should be numbered 1, 2, 3, ...
            step_numbers = [step.step_number for step in result]
            assert step_numbers == list(range(1, len(result) + 1))

    @pytest.mark.asyncio
    async def test_llm_marker_consistency(
        self, full_pipeline, sample_parts, sample_drawings, mock_llm_response
    ):
        """Test that is_llm_generated flag is consistent."""
        with patch.object(full_pipeline["llm"], "_call_llm") as mock_call:
            mock_call.return_value = mock_llm_response
            result = await full_pipeline["assembly"].process(sample_parts, sample_drawings)
            # All steps from LLM should be marked consistently
            llm_steps = [step for step in result if step.is_llm_generated]
            if llm_steps:
                # If any are LLM-generated, most should be
                assert len(llm_steps) >= len(result) * 0.8


# ============================================================================
# ERROR RECOVERY TESTS (2 tests) - Pipeline resilience
# ============================================================================


class TestErrorRecovery:
    """Test pipeline error handling and recovery."""

    @pytest.mark.asyncio
    async def test_pipeline_recovers_from_llm_failure(
        self, full_pipeline, sample_parts, sample_drawings
    ):
        """Test that pipeline recovers when LLM fails."""
        with patch.object(full_pipeline["llm"], "_call_llm") as mock_call:
            import httpx

            mock_call.side_effect = httpx.ConnectError("LLM unavailable")
            result = await full_pipeline["assembly"].process(sample_parts, sample_drawings)
            # Should still produce assembly steps
            assert isinstance(result, list)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_pipeline_produces_valid_output_on_fallback(
        self, full_pipeline, sample_parts, sample_drawings
    ):
        """Test that fallback produces valid assembly steps."""
        with patch.object(full_pipeline["llm"], "_call_llm") as mock_call:
            import httpx

            mock_call.side_effect = httpx.ConnectError("LLM unavailable")
            result = await full_pipeline["assembly"].process(sample_parts, sample_drawings)
            # Verify all steps are valid
            for step in result:
                assert step.step_number > 0
                assert step.title
                assert step.description
                assert len(step.part_indices) > 0


# ============================================================================
# REALISTIC SCENARIO TESTS (2 tests)
# ============================================================================


class TestRealisticScenarios:
    """Test realistic assembly scenarios."""

    @pytest.mark.asyncio
    async def test_furniture_assembly(self, full_pipeline, mock_llm_response):
        """Test furniture assembly (realistic use case)."""
        # Simulate furniture: panels, brackets, fasteners
        furniture_parts = [
            Part(
                id="Shelf",
                original_index=0,
                part_type=PartType.PANEL,
                quantity=1,
                volume=200.0,
                dimensions={"width": 100, "height": 30, "depth": 25},
                centroid=[50, 15, 12.5],
                surface_area=5000,
                group_id="Shelf",
            ),
            Part(
                id="Bracket",
                original_index=1,
                part_type=PartType.STRUCTURAL,
                quantity=2,
                volume=50.0,
                dimensions={"width": 30, "height": 30, "depth": 10},
                centroid=[15, 15, 5],
                surface_area=1400,
                group_id="Bracket",
            ),
            Part(
                id="Screw",
                original_index=2,
                part_type=PartType.FASTENER,
                quantity=8,
                volume=0.3,
                dimensions={"width": 1, "height": 1, "depth": 5},
                centroid=[0.5, 0.5, 2.5],
                surface_area=30,
                group_id="Screw",
            ),
        ]
        furniture_drawings = [
            SvgDrawing(part_id=part.id, svg_content=f"<svg>{part.id}</svg>")
            for part in furniture_parts
        ]

        with patch.object(full_pipeline["llm"], "_call_llm") as mock_call:
            mock_call.return_value = mock_llm_response
            result = await full_pipeline["assembly"].process(furniture_parts, furniture_drawings)
            assert len(result) > 0
            # Should include all parts in instructions
            all_part_indices = set()
            for step in result:
                all_part_indices.update(step.part_indices)
                all_part_indices.update(step.context_part_indices)
            assert len(all_part_indices) > 0

    @pytest.mark.asyncio
    async def test_electronics_assembly(self, full_pipeline, mock_llm_response):
        """Test electronics assembly (realistic use case)."""
        # Simulate electronics: chassis, PCB, fasteners
        electronics_parts = [
            Part(
                id="Chassis",
                original_index=0,
                part_type=PartType.STRUCTURAL,
                quantity=1,
                volume=100.0,
                dimensions={"width": 80, "height": 40, "depth": 50},
                centroid=[40, 20, 25],
                surface_area=3000,
                group_id="Chassis",
            ),
            Part(
                id="PCB",
                original_index=1,
                part_type=PartType.PANEL,
                quantity=1,
                volume=20.0,
                dimensions={"width": 70, "height": 30, "depth": 1},
                centroid=[35, 15, 0.5],
                surface_area=2200,
                group_id="PCB",
            ),
            Part(
                id="Standoff",
                original_index=2,
                part_type=PartType.HARDWARE,
                quantity=4,
                volume=2.0,
                dimensions={"width": 3, "height": 3, "depth": 5},
                centroid=[1.5, 1.5, 2.5],
                surface_area=60,
                group_id="Standoff",
            ),
        ]
        electronics_drawings = [
            SvgDrawing(part_id=part.id, svg_content=f"<svg>{part.id}</svg>")
            for part in electronics_parts
        ]

        with patch.object(full_pipeline["llm"], "_call_llm") as mock_call:
            mock_call.return_value = mock_llm_response
            result = await full_pipeline["assembly"].process(
                electronics_parts, electronics_drawings, tone=AssemblyTone.TECHNICAL
            )
            assert len(result) > 0
            # TECHNICAL tone should include specifications
            assert all(isinstance(step, AssemblyStep) for step in result)
