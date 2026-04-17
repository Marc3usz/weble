"""Tests for Phase 3: ExplodedViewSVGGenerator."""

import pytest
import pytest_asyncio
from app.services.exploded_view_generator import ExplodedViewSVGGenerator, IsometricProjection
from app.models.schemas import Part, PartType, AssemblyStep
import math


# ============================================================================
# FIXTURES
# ============================================================================


@pytest_asyncio.fixture
async def svg_generator():
    """Create an ExplodedViewSVGGenerator instance."""
    return ExplodedViewSVGGenerator()


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
def sample_assembly_step():
    """Create a sample assembly step."""
    return AssemblyStep(
        step_number=1,
        title="Attach base panel",
        description="Attach fasteners to panel",
        part_indices=[0, 1],
        part_roles={0: "base", 1: "fastener"},
        context_part_indices=[2],
        assembly_sequence=["Align", "Insert", "Secure"],
        warnings=["Do not overtighten"],
        tips=["Use a level"],
        duration_minutes=5,
    )


# ============================================================================
# ISOMETRIC PROJECTION TESTS (3 tests)
# ============================================================================


class TestIsometricProjection:
    """Test isometric projection mathematics."""

    def test_project_point_origin(self):
        """Test projection of origin point."""
        x, y = IsometricProjection.project_point(0, 0, 0)
        assert x == 0
        assert y == 0

    def test_project_point_x_axis(self):
        """Test projection of X-axis point."""
        x, y = IsometricProjection.project_point(1, 0, 0, scale=1.0)
        # Should go right and slightly down (30° angle)
        assert x > 0
        assert y > 0

    def test_project_point_z_axis(self):
        """Test projection of Z-axis point (vertical)."""
        x, y = IsometricProjection.project_point(0, 0, 1, scale=1.0)
        # Should go straight up
        assert x == 0
        assert y < 0  # y increases downward in SVG


class TestIsometricBox:
    """Test isometric box projection."""

    def test_project_box_returns_8_vertices(self):
        """Test that box projection returns all 8 vertices."""
        vertices = IsometricProjection.project_box(0, 0, 0, 10, 10, 10, scale=1.0)
        assert len(vertices) == 8
        assert all(isinstance(coord, tuple) and len(coord) == 2 for coord in vertices.values())

    def test_project_box_vertex_names(self):
        """Test that box projection uses correct vertex naming."""
        vertices = IsometricProjection.project_box(0, 0, 0, 10, 10, 10, scale=1.0)
        expected_names = ["v0", "v1", "v2", "v3", "v4", "v5", "v6", "v7"]
        assert all(name in vertices for name in expected_names)

    def test_project_box_respects_scale(self):
        """Test that scale parameter affects projection."""
        vertices_1x = IsometricProjection.project_box(0, 0, 0, 10, 10, 10, scale=1.0)
        vertices_2x = IsometricProjection.project_box(0, 0, 0, 10, 10, 10, scale=2.0)
        # With 2x scale, distances should roughly double
        dist_1x = math.sqrt(vertices_1x["v6"][0] ** 2 + vertices_1x["v6"][1] ** 2)
        dist_2x = math.sqrt(vertices_2x["v6"][0] ** 2 + vertices_2x["v6"][1] ** 2)
        assert dist_2x > dist_1x


# ============================================================================
# SVG GENERATION TESTS (5 tests)
# ============================================================================


class TestSVGGeneration:
    """Test SVG generation for exploded views."""

    @pytest.mark.asyncio
    async def test_generate_returns_svg_string(
        self, svg_generator, sample_parts, sample_assembly_step
    ):
        """Test that generation returns valid SVG string."""
        svg = await svg_generator.generate_exploded_view(sample_parts, sample_assembly_step)
        assert isinstance(svg, str)
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")

    @pytest.mark.asyncio
    async def test_generate_includes_step_number(
        self, svg_generator, sample_parts, sample_assembly_step
    ):
        """Test that SVG includes step number."""
        svg = await svg_generator.generate_exploded_view(sample_parts, sample_assembly_step)
        assert "Step 1" in svg

    @pytest.mark.asyncio
    async def test_generate_includes_step_title(
        self, svg_generator, sample_parts, sample_assembly_step
    ):
        """Test that SVG includes step title."""
        svg = await svg_generator.generate_exploded_view(sample_parts, sample_assembly_step)
        assert "Attach base panel" in svg

    @pytest.mark.asyncio
    async def test_generate_includes_part_labels(
        self, svg_generator, sample_parts, sample_assembly_step
    ):
        """Test that SVG includes part labels."""
        svg = await svg_generator.generate_exploded_view(sample_parts, sample_assembly_step)
        # Active parts should be rendered with labels
        assert "Part A" in svg or ">A<" in svg or '"A"' in svg

    @pytest.mark.asyncio
    async def test_generate_valid_svg_structure(
        self, svg_generator, sample_parts, sample_assembly_step
    ):
        """Test that generated SVG has valid structure."""
        svg = await svg_generator.generate_exploded_view(sample_parts, sample_assembly_step)
        # Should contain required SVG elements
        assert "<svg" in svg
        assert 'xmlns="http://www.w3.org/2000/svg"' in svg
        assert "</svg>" in svg
        assert "<g" in svg  # Should have groups
        assert "</g>" in svg


# ============================================================================
# HIGHLIGHTING TESTS (4 tests)
# ============================================================================


class TestPartHighlighting:
    """Test active vs. context part highlighting."""

    @pytest.mark.asyncio
    async def test_active_parts_full_opacity(self, svg_generator, sample_parts):
        """Test that active parts have full opacity."""
        step = AssemblyStep(
            step_number=1,
            title="Test",
            description="Test",
            part_indices=[0],  # Part A is active
            part_roles={0: "base"},
            context_part_indices=[],
        )
        svg = await svg_generator.generate_exploded_view(sample_parts, step)
        # SVG should distinguish active part (full opacity)
        assert 'opacity="1' in svg or "opacity: 1" in svg or "part-active" in svg

    @pytest.mark.asyncio
    async def test_context_parts_reduced_opacity(self, svg_generator, sample_parts):
        """Test that context parts have reduced opacity."""
        step = AssemblyStep(
            step_number=1,
            title="Test",
            description="Test",
            part_indices=[0],
            part_roles={0: "base"},
            context_part_indices=[1, 2],  # Parts B and C are context
        )
        svg = await svg_generator.generate_exploded_view(sample_parts, step)
        # SVG should distinguish context parts (low opacity or class)
        assert 'opacity="0.3' in svg or "part-context" in svg or "opacity: 0.3" in svg

    @pytest.mark.asyncio
    async def test_different_colors_by_part_type(self, svg_generator, sample_parts):
        """Test that different part types get different colors."""
        step = AssemblyStep(
            step_number=1,
            title="Test",
            description="Test",
            part_indices=[0, 1, 2],  # All parts active
            part_roles={0: "base", 1: "fastener", 2: "structural"},
            context_part_indices=[],
        )
        svg = await svg_generator.generate_exploded_view(sample_parts, step)
        # Should have multiple fill colors
        fill_colors = ["#4a90e2", "#f5a623", "#7ed321"]  # Panel, fastener, structural
        has_colors = sum(1 for color in fill_colors if color in svg)
        assert has_colors >= 2  # At least 2 different colors

    @pytest.mark.asyncio
    async def test_quantity_displayed(self, svg_generator):
        """Test that quantity is displayed for parts."""
        parts = [
            Part(
                id="X",
                original_index=0,
                part_type=PartType.FASTENER,
                quantity=8,
                volume=1.0,
                dimensions={"width": 3, "height": 3, "depth": 10},
                centroid=[1.5, 1.5, 5],
                surface_area=120,
                group_id="X",
            )
        ]
        step = AssemblyStep(
            step_number=1,
            title="Test",
            description="Test",
            part_indices=[0],
            part_roles={0: "fastener"},
        )
        svg = await svg_generator.generate_exploded_view(parts, step)
        # Quantity should be displayed
        assert "×8" in svg or "x8" in svg or "8" in svg


# ============================================================================
# ASSEMBLY SEQUENCE TESTS (2 tests)
# ============================================================================


class TestAssemblySequence:
    """Test assembly sequence rendering."""

    @pytest.mark.asyncio
    async def test_assembly_sequence_included(
        self, svg_generator, sample_parts, sample_assembly_step
    ):
        """Test that assembly sequence is included in SVG."""
        svg = await svg_generator.generate_exploded_view(sample_parts, sample_assembly_step)
        # Should include sequence steps
        assert "Align" in svg
        assert "Insert" in svg
        assert "Secure" in svg

    @pytest.mark.asyncio
    async def test_warnings_included(self, svg_generator, sample_parts, sample_assembly_step):
        """Test that warnings are included in SVG."""
        svg = await svg_generator.generate_exploded_view(sample_parts, sample_assembly_step)
        # Should include warnings
        assert "Do not overtighten" in svg or "Do not" in svg


# ============================================================================
# VALIDATION TESTS (2 tests)
# ============================================================================


class TestValidation:
    """Test input validation."""

    @pytest.mark.asyncio
    async def test_validate_valid_input(self, svg_generator, sample_parts, sample_assembly_step):
        """Test validation of valid input."""
        result = await svg_generator.validate_input((sample_parts, sample_assembly_step))
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_empty_parts(self, svg_generator, sample_assembly_step):
        """Test validation fails for empty parts."""
        result = await svg_generator.validate_input(([], sample_assembly_step))
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_empty_part_indices(self, svg_generator, sample_parts):
        """Test validation fails when step has no part indices."""
        step = AssemblyStep(
            step_number=1,
            title="Test",
            description="Test",
            part_indices=[],  # Empty!
            part_roles={},
        )
        result = await svg_generator.validate_input((sample_parts, step))
        assert result is False


# ============================================================================
# EDGE CASE TESTS (3 tests)
# ============================================================================


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_single_part_assembly(self, svg_generator):
        """Test assembly with single part."""
        parts = [
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
        step = AssemblyStep(
            step_number=1,
            title="Place base",
            description="Place the base panel",
            part_indices=[0],
            part_roles={0: "base"},
        )
        svg = await svg_generator.generate_exploded_view(parts, step)
        assert isinstance(svg, str)
        assert "Place base" in svg

    @pytest.mark.asyncio
    async def test_many_parts_assembly(self, svg_generator):
        """Test assembly with many parts."""
        parts = [
            Part(
                id=chr(65 + i),  # A, B, C, ...
                original_index=i,
                part_type=PartType.FASTENER,
                quantity=1,
                volume=1.0,
                dimensions={"width": 3, "height": 3, "depth": 10},
                centroid=[1.5, 1.5, 5],
                surface_area=120,
                group_id=chr(65 + i),
            )
            for i in range(10)
        ]
        step = AssemblyStep(
            step_number=1,
            title="Complex assembly",
            description="Assemble many parts",
            part_indices=list(range(10)),
            part_roles={i: "fastener" for i in range(10)},
        )
        svg = await svg_generator.generate_exploded_view(parts, step)
        assert isinstance(svg, str)
        assert "Complex assembly" in svg

    @pytest.mark.asyncio
    async def test_no_assembly_sequence(self, svg_generator, sample_parts):
        """Test step without assembly sequence."""
        step = AssemblyStep(
            step_number=1,
            title="Simple step",
            description="Simple step",
            part_indices=[0],
            part_roles={0: "base"},
            assembly_sequence=[],  # Empty sequence
        )
        svg = await svg_generator.generate_exploded_view(sample_parts, step)
        assert isinstance(svg, str)
        assert "Simple step" in svg


# ============================================================================
# CANVAS SIZE TESTS (2 tests)
# ============================================================================


class TestCanvasSize:
    """Test canvas sizing logic."""

    def test_canvas_size_grows_with_parts(self, svg_generator):
        """Test that canvas size increases with number of parts."""
        few_parts = [
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
        many_parts = few_parts * 5

        w1, h1 = svg_generator._calculate_canvas_size(few_parts)
        w2, h2 = svg_generator._calculate_canvas_size(many_parts)

        assert w2 >= w1
        assert h2 >= h1

    def test_canvas_size_within_bounds(self, svg_generator, sample_parts):
        """Test that canvas size stays within reasonable bounds."""
        w, h = svg_generator._calculate_canvas_size(sample_parts)
        assert 200 <= w <= 2000
        assert 200 <= h <= 2000
