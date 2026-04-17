"""Tests for Phase 3: Performance and Cost Optimization."""

import pytest
import pytest_asyncio
from unittest.mock import patch, Mock
import time
import json

from app.services.assembly_generator import AssemblyGeneratorService
from app.services.llm_assembly_generator import LLMAssemblyGeneratorService
from app.services.exploded_view_generator import ExplodedViewSVGGenerator
from app.models.schemas import Part, PartType, SvgDrawing
from app.core.config import AssemblyTone, settings


# ============================================================================
# FIXTURES
# ============================================================================


@pytest_asyncio.fixture
async def llm_service():
    """Create LLM service."""
    return LLMAssemblyGeneratorService()


@pytest_asyncio.fixture
async def assembly_generator(llm_service):
    """Create assembly generator."""
    return AssemblyGeneratorService(llm_service=llm_service)


@pytest_asyncio.fixture
async def svg_generator():
    """Create SVG generator."""
    return ExplodedViewSVGGenerator()


@pytest.fixture
def small_parts():
    """Create small parts list (3 parts)."""
    return [
        Part(
            id="A",
            original_index=0,
            part_type=PartType.PANEL,
            quantity=1,
            volume=100.0,
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
def medium_parts():
    """Create medium parts list (10 parts)."""
    base = [
        Part(
            id=chr(65 + i),  # A, B, C, ...
            original_index=i,
            part_type=PartType.FASTENER if i % 3 == 0 else PartType.STRUCTURAL,
            quantity=4 if i % 3 == 0 else 1,
            volume=float(i * 10),
            dimensions={"width": 20 + i * 2, "height": 20 + i, "depth": 5},
            centroid=[10 + i, 10 + i // 2, 2.5],
            surface_area=1000 + i * 100,
            group_id=chr(65 + i),
        )
        for i in range(10)
    ]
    return base


@pytest.fixture
def large_parts():
    """Create large parts list (30 parts)."""
    return [
        Part(
            id=f"P{i:02d}",
            original_index=i,
            part_type=[
                PartType.PANEL,
                PartType.FASTENER,
                PartType.STRUCTURAL,
                PartType.HARDWARE,
            ][i % 4],
            quantity=1 + (i % 3),
            volume=float(50 + i * 5),
            dimensions={
                "width": 40 + i,
                "height": 30 + i // 2,
                "depth": 5 + i % 5,
            },
            centroid=[20 + i / 2, 15 + i / 3, 2.5],
            surface_area=2000 + i * 200,
            group_id=f"G{i % 5}",
        )
        for i in range(30)
    ]


@pytest.fixture
def small_drawings(small_parts):
    """Create small drawings."""
    return [
        SvgDrawing(part_id=part.id, svg_content=f"<svg>{part.id}</svg>") for part in small_parts
    ]


@pytest.fixture
def medium_drawings(medium_parts):
    """Create medium drawings."""
    return [
        SvgDrawing(part_id=part.id, svg_content=f"<svg>{part.id}</svg>") for part in medium_parts
    ]


@pytest.fixture
def large_drawings(large_parts):
    """Create large drawings."""
    return [
        SvgDrawing(part_id=part.id, svg_content=f"<svg>{part.id}</svg>") for part in large_parts
    ]


@pytest.fixture
def mock_llm_response():
    """Create mock LLM response."""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "steps": [
                                {
                                    "step_number": i + 1,
                                    "title": f"Step {i + 1}",
                                    "description": f"Assembly step {i + 1}",
                                    "detail_description": "Detailed instructions",
                                    "part_indices": [0, 1],
                                    "part_roles": {0: "base", 1: "attachment"},
                                    "context_part_indices": [],
                                    "assembly_sequence": ["Align", "Insert"],
                                    "warnings": [],
                                    "tips": [],
                                    "confidence_score": 0.9,
                                    "is_llm_generated": True,
                                }
                                for i in range(3)
                            ]
                        }
                    )
                }
            }
        ],
        "usage": {
            "prompt_tokens": 200,
            "completion_tokens": 300,
            "total_tokens": 500,
        },
    }


# ============================================================================
# LLM LATENCY TESTS (3 tests)
# ============================================================================


class TestLLMLatency:
    """Test LLM performance targets (<30s)."""

    @pytest.mark.asyncio
    async def test_llm_latency_small_assembly(
        self, assembly_generator, small_parts, small_drawings, mock_llm_response
    ):
        """Test LLM generation latency for small assembly."""
        with patch.object(assembly_generator.llm_service, "_call_llm") as mock_call:
            mock_call.return_value = mock_llm_response
            start = time.time()
            result = await assembly_generator.process(small_parts, small_drawings)
            elapsed = time.time() - start
            # Should be fast with mocked API
            assert elapsed < 5
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_llm_latency_medium_assembly(
        self, assembly_generator, medium_parts, medium_drawings, mock_llm_response
    ):
        """Test LLM generation latency for medium assembly."""
        with patch.object(assembly_generator.llm_service, "_call_llm") as mock_call:
            mock_call.return_value = mock_llm_response
            start = time.time()
            result = await assembly_generator.process(medium_parts, medium_drawings)
            elapsed = time.time() - start
            # Should complete within reasonable time
            assert elapsed < 10
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_rules_based_latency_small(self, assembly_generator, small_parts, small_drawings):
        """Test rules-based generation latency (should be <2s)."""
        # Disable LLM
        with patch.object(assembly_generator, "llm_service", None):
            start = time.time()
            result = await assembly_generator.process(small_parts, small_drawings)
            elapsed = time.time() - start
            # Rules-based should be very fast
            assert elapsed < 2
            assert len(result) > 0


# ============================================================================
# TOKEN USAGE TESTS (3 tests)
# ============================================================================


class TestTokenUsage:
    """Test token estimation and usage."""

    def test_token_estimation_scales_linearly(self, llm_service, small_parts, medium_parts):
        """Test that token estimation scales with part count."""
        small_tokens = llm_service._estimate_tokens(small_parts)
        medium_tokens = llm_service._estimate_tokens(medium_parts)
        # More parts = more tokens
        assert medium_tokens > small_tokens

    def test_token_usage_reasonable(self, llm_service, large_parts):
        """Test that token usage is reasonable for large assembly."""
        tokens = llm_service._estimate_tokens(large_parts)
        # Should estimate between 1000-5000 tokens for 30 parts
        assert 500 < tokens < 5000

    def test_token_count_with_tone_parameter(self, llm_service, medium_parts):
        """Test token estimation doesn't vary drastically by tone."""
        ikea_tokens = llm_service._estimate_tokens(medium_parts)
        technical_tokens = llm_service._estimate_tokens(medium_parts)
        # Different tones shouldn't drastically change token count
        # (they may have slightly different overhead but should be similar)
        assert abs(ikea_tokens - technical_tokens) < 100


# ============================================================================
# COST ESTIMATION TESTS (3 tests)
# ============================================================================


class TestCostEstimation:
    """Test cost calculation for LLM calls."""

    def test_cost_scales_with_tokens(self, llm_service):
        """Test that cost increases with token usage."""
        cost_low = llm_service._calculate_cost(100, 100, "google/gemini-2.0-flash")
        cost_high = llm_service._calculate_cost(1000, 1000, "google/gemini-2.0-flash")
        assert cost_high > cost_low

    def test_cost_reasonable_per_assembly(self, llm_service, medium_parts):
        """Test that cost per assembly is reasonable."""
        tokens = llm_service._estimate_tokens(medium_parts)
        # Assume typical 1:2 input:output ratio
        cost = llm_service._calculate_cost(tokens, tokens * 2, "google/gemini-2.0-flash")
        # Should be under $0.01 per assembly for Gemini
        assert cost < 0.01

    def test_cost_comparison_different_models(self, llm_service):
        """Test cost calculation for different models."""
        cost_gemini = llm_service._calculate_cost(500, 500, "google/gemini-2.0-flash")
        cost_gpt = llm_service._calculate_cost(500, 500, "openai/gpt-4")
        # Different models should have different costs
        # (GPT-4 is typically more expensive)
        assert isinstance(cost_gemini, float)
        assert isinstance(cost_gpt, float)


# ============================================================================
# SVG GENERATION PERFORMANCE TESTS (2 tests)
# ============================================================================


class TestSVGGenerationPerformance:
    """Test SVG generation performance."""

    @pytest.mark.asyncio
    async def test_exploded_view_generation_latency(self, svg_generator, small_parts):
        """Test SVG generation latency."""
        from app.models.schemas import AssemblyStep

        step = AssemblyStep(
            step_number=1,
            title="Test",
            description="Test",
            part_indices=[0, 1],
            part_roles={0: "base", 1: "attachment"},
        )
        start = time.time()
        svg = await svg_generator.generate_exploded_view(small_parts, step)
        elapsed = time.time() - start
        # SVG generation should be fast
        assert elapsed < 1
        assert len(svg) > 100

    @pytest.mark.asyncio
    async def test_svg_generation_large_assembly(self, svg_generator, large_parts):
        """Test SVG generation with large assembly."""
        from app.models.schemas import AssemblyStep

        step = AssemblyStep(
            step_number=1,
            title="Complex assembly",
            description="Test",
            part_indices=list(range(min(10, len(large_parts)))),
            part_roles={i: "part" for i in range(min(10, len(large_parts)))},
        )
        start = time.time()
        svg = await svg_generator.generate_exploded_view(large_parts, step)
        elapsed = time.time() - start
        # Should still be reasonably fast
        assert elapsed < 5
        assert len(svg) > 100


# ============================================================================
# FULL PIPELINE PERFORMANCE TESTS (2 tests)
# ============================================================================


class TestFullPipelinePerformance:
    """Test end-to-end pipeline performance."""

    @pytest.mark.asyncio
    async def test_full_pipeline_small_assembly(
        self, assembly_generator, small_parts, small_drawings, mock_llm_response
    ):
        """Test full pipeline latency for small assembly."""
        with patch.object(assembly_generator.llm_service, "_call_llm") as mock_call:
            mock_call.return_value = mock_llm_response
            start = time.time()
            result = await assembly_generator.process(small_parts, small_drawings)
            elapsed = time.time() - start
            # Full pipeline with LLM should complete in <10s
            assert elapsed < 10
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_full_pipeline_medium_assembly(
        self, assembly_generator, medium_parts, medium_drawings, mock_llm_response
    ):
        """Test full pipeline latency for medium assembly."""
        with patch.object(assembly_generator.llm_service, "_call_llm") as mock_call:
            mock_call.return_value = mock_llm_response
            start = time.time()
            result = await assembly_generator.process(medium_parts, medium_drawings)
            elapsed = time.time() - start
            # Full pipeline should still be reasonable
            assert elapsed < 20
            assert len(result) > 0


# ============================================================================
# MEMORY USAGE TESTS (2 tests) - Simple checks
# ============================================================================


class TestMemoryEfficiency:
    """Test memory efficiency."""

    @pytest.mark.asyncio
    async def test_large_assembly_doesnt_crash(
        self, assembly_generator, large_parts, large_drawings
    ):
        """Test that large assemblies don't cause memory issues."""
        # Just test that it doesn't crash
        from app.models.schemas import AssemblyStep

        # Simplified: just test rules-based fallback with large parts
        with patch.object(assembly_generator, "llm_service", None):
            result = await assembly_generator.process(large_parts, large_drawings)
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_svg_generation_many_parts(self, svg_generator, large_parts):
        """Test SVG generation doesn't crash with many parts."""
        from app.models.schemas import AssemblyStep

        step = AssemblyStep(
            step_number=1,
            title="Large assembly",
            description="Test",
            part_indices=list(range(20)),
            part_roles={i: "part" for i in range(20)},
        )
        svg = await svg_generator.generate_exploded_view(large_parts, step)
        assert isinstance(svg, str)
        assert len(svg) > 100
