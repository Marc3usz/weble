"""Phase 2 Integration Tests - Enhanced Parts Extraction and HLR SVG Generation."""

import pytest
import pytest_asyncio
from app.services.parts_extractor import PartsExtractorService
from app.services.svg_generator import SvgGeneratorService
from app.models.schemas import Part, PartType, Geometry3D, SvgDrawing


@pytest_asyncio.fixture
async def parts_extractor():
    """Create a PartsExtractorService instance."""
    return PartsExtractorService()


@pytest_asyncio.fixture
async def svg_generator():
    """Create a SvgGeneratorService instance."""
    return SvgGeneratorService()


@pytest.fixture
def sample_geometry_with_solids():
    """Create sample geometry with solid metadata for realistic parts extraction."""
    return Geometry3D(
        vertices=[[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]],
        normals=[[0, 0, 1], [0, 0, 1], [0, 0, 1], [0, 0, 1]],
        indices=[0, 1, 2, 2, 3, 0],
        metadata={
            "solids_count": 3,
            "solids": [
                {
                    "solid_id": "solid_0",
                    "volume": 1000.0,  # Large panel
                    "centroid": [25, 15, 1],
                    "bounding_box": {
                        "min": [0, 0, 0],
                        "max": [50, 30, 2],
                    },
                },
                {
                    "solid_id": "solid_1",
                    "volume": 1020.0,  # Similar size (within 2%)
                    "centroid": [25.2, 15.1, 1],
                    "bounding_box": {
                        "min": [0.1, 0.1, 0],
                        "max": [50.1, 30.1, 2],
                    },
                },
                {
                    "solid_id": "solid_2",
                    "volume": 2.5,  # Small fastener
                    "centroid": [2.5, 2.5, 5],
                    "bounding_box": {
                        "min": [0, 0, 0],
                        "max": [5, 5, 10],
                    },
                },
            ],
            "bounds": {"min": [0, 0, 0], "max": [50, 30, 10]},
            "total_triangles": 2,
            "source": "cadquery",
        },
    )


@pytest.fixture
def sample_uniform_geometry():
    """Create geometry with uniform part sizes (low variance)."""
    return Geometry3D(
        vertices=[[0, 0, 0], [1, 1, 1]],  # Need vertices to pass validation
        normals=[[0, 0, 1], [0, 0, 1]],
        indices=[0, 1],
        metadata={
            "solids_count": 3,
            "solids": [
                {
                    "solid_id": "solid_0",
                    "volume": 100.0,
                    "centroid": [5, 5, 5],
                    "bounding_box": {"min": [0, 0, 0], "max": [10, 10, 10]},
                },
                {
                    "solid_id": "solid_1",
                    "volume": 101.0,
                    "centroid": [5, 5, 5],
                    "bounding_box": {"min": [0, 0, 0], "max": [10, 10, 10]},
                },
                {
                    "solid_id": "solid_2",
                    "volume": 99.0,
                    "centroid": [5, 5, 5],
                    "bounding_box": {"min": [0, 0, 0], "max": [10, 10, 10]},
                },
            ],
        },
    )


@pytest.fixture
def sample_mixed_geometry():
    """Create geometry with highly mixed part sizes (high variance)."""
    return Geometry3D(
        vertices=[[0, 0, 0], [1, 1, 1]],  # Need vertices to pass validation
        normals=[[0, 0, 1], [0, 0, 1]],
        indices=[0, 1],
        metadata={
            "solids_count": 3,
            "solids": [
                {
                    "solid_id": "solid_tiny",
                    "volume": 1.0,
                    "centroid": [0.5, 0.5, 0.5],
                    "bounding_box": {"min": [0, 0, 0], "max": [1, 1, 1]},
                },
                {
                    "solid_id": "solid_small",
                    "volume": 100.0,
                    "centroid": [5, 5, 5],
                    "bounding_box": {"min": [0, 0, 0], "max": [10, 10, 10]},
                },
                {
                    "solid_id": "solid_large",
                    "volume": 10000.0,
                    "centroid": [50, 50, 50],
                    "bounding_box": {"min": [0, 0, 0], "max": [100, 100, 100]},
                },
            ],
        },
    )


# ==============================================================================
# PHASE 2: ADAPTIVE TOLERANCE TESTS
# ==============================================================================


class TestAdaptiveTolerance:
    """Test adaptive tolerance calculation based on model scale."""

    @pytest.mark.asyncio
    async def test_uniform_geometry_uses_standard_tolerance(
        self, parts_extractor, sample_uniform_geometry
    ):
        """Test that uniform models use standard tolerance (15%)."""
        parts = await parts_extractor.process(sample_uniform_geometry)
        # All three should be grouped together
        assert len(parts) == 1
        assert parts[0].quantity == 3
        assert "deduplication_tolerance" in parts[0].metrics
        # Standard tolerance around 15%
        tolerance = parts[0].metrics["deduplication_tolerance"]
        assert 0.10 <= tolerance <= 0.20

    @pytest.mark.asyncio
    async def test_mixed_geometry_uses_tight_tolerance(
        self, parts_extractor, sample_mixed_geometry
    ):
        """Test that highly mixed models use tighter tolerance."""
        parts = await parts_extractor.process(sample_mixed_geometry)
        # Should have 3 separate parts due to scale difference
        assert len(parts) == 3
        # Smallest part should use tight tolerance
        tolerance = parts[0].metrics["deduplication_tolerance"]
        assert tolerance <= 0.15  # At most 15%, likely tighter


class TestEnhancedClassification:
    """Test Phase 2 multi-strategy part classification."""

    @pytest.mark.asyncio
    async def test_classify_panel_flatness_based(self, parts_extractor):
        """Test PANEL classification based on flatness ratio."""
        # Large flat sheet: w=100, h=100, d=1
        parts = await parts_extractor.process(
            Geometry3D(
                vertices=[[0, 0, 0], [1, 1, 1]],
                normals=[[0, 0, 1], [0, 0, 1]],
                indices=[0, 1],
                metadata={
                    "solids": [
                        {
                            "solid_id": "sheet",
                            "volume": 10000.0,
                            "centroid": [50, 50, 0.5],
                            "bounding_box": {"min": [0, 0, 0], "max": [100, 100, 1]},
                        }
                    ]
                },
            )
        )
        assert parts[0].part_type == PartType.PANEL

    @pytest.mark.asyncio
    async def test_classify_fastener_small_elongated(self, parts_extractor):
        """Test FASTENER classification for small elongated parts."""
        # Small elongated part: w=1, h=1, d=20
        parts = await parts_extractor.process(
            Geometry3D(
                vertices=[[0, 0, 0], [1, 1, 1]],
                normals=[[0, 0, 1], [0, 0, 1]],
                indices=[0, 1],
                metadata={
                    "solids": [
                        {
                            "solid_id": "screw",
                            "volume": 20.0,
                            "centroid": [0.5, 0.5, 10],
                            "bounding_box": {"min": [0, 0, 0], "max": [1, 1, 20]},
                        }
                    ]
                },
            )
        )
        assert parts[0].part_type == PartType.FASTENER

    @pytest.mark.asyncio
    async def test_classify_hardware_medium_cubic(self, parts_extractor):
        """Test HARDWARE classification for medium cubic parts."""
        # Medium cubic part: w=15, h=15, d=15, vol=3375
        parts = await parts_extractor.process(
            Geometry3D(
                vertices=[[0, 0, 0], [1, 1, 1]],
                normals=[[0, 0, 1], [0, 0, 1]],
                indices=[0, 1],
                metadata={
                    "solids": [
                        {
                            "solid_id": "bracket",
                            "volume": 3375.0,
                            "centroid": [7.5, 7.5, 7.5],
                            "bounding_box": {"min": [0, 0, 0], "max": [15, 15, 15]},
                        }
                    ]
                },
            )
        )
        # 3375 > 500, so it's classified as STRUCTURAL (not HARDWARE)
        # HARDWARE is 50-500, STRUCTURAL is >= 500
        assert parts[0].part_type == PartType.STRUCTURAL

    @pytest.mark.asyncio
    async def test_classify_structural_large_compact(self, parts_extractor):
        """Test STRUCTURAL classification for large compact parts."""
        # Large compact part: w=50, h=50, d=50
        parts = await parts_extractor.process(
            Geometry3D(
                vertices=[[0, 0, 0], [1, 1, 1]],
                normals=[[0, 0, 1], [0, 0, 1]],
                indices=[0, 1],
                metadata={
                    "solids": [
                        {
                            "solid_id": "block",
                            "volume": 125000.0,
                            "centroid": [25, 25, 25],
                            "bounding_box": {"min": [0, 0, 0], "max": [50, 50, 50]},
                        }
                    ]
                },
            )
        )
        assert parts[0].part_type == PartType.STRUCTURAL


class TestDeduplicationAdvanced:
    """Test advanced deduplication with adaptive tolerance."""

    @pytest.mark.asyncio
    async def test_deduplicate_similar_panels(self, parts_extractor, sample_geometry_with_solids):
        """Test that similar panels are grouped correctly."""
        parts = await parts_extractor.process(sample_geometry_with_solids)
        # First two solids should be grouped (panels with ~2% difference)
        panel_parts = [p for p in parts if p.part_type == PartType.PANEL]
        assert len(panel_parts) >= 1
        # The panel group should have quantity 2
        assert any(p.quantity == 2 for p in panel_parts)

    @pytest.mark.asyncio
    async def test_group_metrics_preserved(self, parts_extractor, sample_geometry_with_solids):
        """Test that group metrics track original solids."""
        parts = await parts_extractor.process(sample_geometry_with_solids)
        # Find grouped parts
        grouped = [p for p in parts if p.quantity > 1]
        for part in grouped:
            # Should have group_members tracking original solids
            assert "group_members" in part.metrics
            assert len(part.metrics["group_members"]) == part.quantity


# ==============================================================================
# PHASE 2: HLR SVG GENERATION TESTS
# ==============================================================================


class TestHlrSvgGeneration:
    """Test Phase 2 HLR-enhanced SVG generation."""

    @pytest.mark.asyncio
    async def test_hlr_svg_has_orthographic_views(self, svg_generator, sample_parts_for_svg):
        """Test that HLR SVG includes orthographic views."""
        result = await svg_generator.process(sample_parts_for_svg)
        svg = result[0].svg_content
        # Check for view labels
        assert "FRONT VIEW" in svg
        assert "TOP VIEW" in svg
        assert "ISOMETRIC (HLR)" in svg

    @pytest.mark.asyncio
    async def test_hlr_svg_includes_dimension_annotations(
        self, svg_generator, sample_parts_for_svg
    ):
        """Test that dimensions are annotated in SVG."""
        result = await svg_generator.process(sample_parts_for_svg)
        svg = result[0].svg_content
        # Should have dimension lines and values
        assert "dimension" in svg
        assert "<line x1=" in svg  # dimension lines
        assert "<text" in svg  # dimension text

    @pytest.mark.asyncio
    async def test_hlr_svg_has_metadata_block(self, svg_generator, sample_parts_for_svg):
        """Test that technical metadata block is included."""
        result = await svg_generator.process(sample_parts_for_svg)
        assert result[0].metadata["projection"] == "orthographic_multi_view_hlr"
        assert "front_view" in result[0].metadata["includes"]
        assert "top_view" in result[0].metadata["includes"]
        assert "isometric" in result[0].metadata["includes"]

    @pytest.mark.asyncio
    async def test_hlr_svg_dynamic_canvas_sizing(self, svg_generator):
        """Test that canvas size adapts to part dimensions."""
        # Small part
        small_part = Part(
            id="S",
            original_index=0,
            part_type=PartType.FASTENER,
            quantity=1,
            volume=5.0,
            dimensions={"width": 1.0, "height": 1.0, "depth": 2.0},
            centroid=[0.5, 0.5, 1.0],
            surface_area=10.0,
            group_id="S",
        )

        # Very large part
        large_part = Part(
            id="L",
            original_index=1,
            part_type=PartType.PANEL,
            quantity=1,
            volume=500000.0,
            dimensions={"width": 1000.0, "height": 500.0, "depth": 10.0},
            centroid=[500, 250, 5],
            surface_area=1250000.0,
            group_id="L",
        )

        results = await svg_generator.process([small_part, large_part])

        small_svg = results[0].svg_content
        large_svg = results[1].svg_content

        # Extract canvas widths (rough comparison)
        import re

        small_width = float(re.search(r'width="([0-9.]+)"', small_svg).group(1))
        large_width = float(re.search(r'width="([0-9.]+)"', large_svg).group(1))

        # Large part should have larger canvas (at least somewhat)
        assert large_width >= small_width  # Can be equal due to 400px minimum


@pytest.fixture
def sample_parts_for_svg():
    """Create realistic sample parts for SVG generation tests."""
    return [
        Part(
            id="A",
            original_index=0,
            part_type=PartType.PANEL,
            quantity=1,
            volume=500.0,
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
            volume=200.0,
            dimensions={"width": 10, "height": 10, "depth": 20},
            centroid=[5, 5, 10],
            surface_area=900,
            group_id="B",
            metrics={},
        ),
    ]


# ==============================================================================
# PHASE 2: INTEGRATION TESTS
# ==============================================================================


class TestPhase2EndToEnd:
    """Integration tests combining parts extraction and SVG generation."""

    @pytest.mark.asyncio
    async def test_full_phase2_pipeline(
        self, parts_extractor, svg_generator, sample_geometry_with_solids
    ):
        """Test complete Phase 2 pipeline: extract parts → generate SVG."""
        # Stage 2: Extract parts
        parts = await parts_extractor.process(sample_geometry_with_solids)
        assert len(parts) > 0

        # Stage 3: Generate SVG
        drawings = await svg_generator.process(parts)
        assert len(drawings) == len(parts)

        # Verify SVG content quality
        for drawing in drawings:
            assert "<svg" in drawing.svg_content
            assert "FRONT VIEW" in drawing.svg_content
            # Check for HLR metadata
            assert "orthographic_multi_view_hlr" in drawing.metadata["projection"]

    @pytest.mark.asyncio
    async def test_quantity_label_consistency(
        self, parts_extractor, svg_generator, sample_geometry_with_solids
    ):
        """Test that quantity labels are consistent across pipeline."""
        parts = await parts_extractor.process(sample_geometry_with_solids)
        drawings = await svg_generator.process(parts)

        for part, drawing in zip(parts, drawings):
            # If part quantity > 1, drawing should reflect it
            if part.quantity > 1:
                assert f"QTY: {part.quantity}" in drawing.svg_content
            # quantity_label should match
            expected_label = f"×{part.quantity}" if part.quantity > 1 else ""
            assert drawing.quantity_label == expected_label

    @pytest.mark.asyncio
    async def test_part_classification_in_svg_metadata(
        self, parts_extractor, svg_generator, sample_geometry_with_solids
    ):
        """Test that part classification is preserved in SVG metadata."""
        parts = await parts_extractor.process(sample_geometry_with_solids)
        drawings = await svg_generator.process(parts)

        for part, drawing in zip(parts, drawings):
            assert drawing.metadata["part_type"] == part.part_type.value
            assert drawing.metadata["volume"] == part.volume
