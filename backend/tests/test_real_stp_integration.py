"""Integration tests using the real STEP file from repo root."""

from pathlib import Path

import pytest

from app.services.assembly_generator import AssemblyGeneratorService
from app.services.parts_extractor import PartsExtractorService
from app.services.step_loader import StepLoaderService
from app.services.svg_generator import SvgGeneratorService


@pytest.fixture
def real_step_file_bytes() -> bytes:
    """Load the real STEP file used for local integration testing."""
    step_path = Path(__file__).resolve().parents[2] / "biurko standard.step"
    assert step_path.exists(), f"Expected STEP file not found: {step_path}"
    data = step_path.read_bytes()
    assert len(data) > 100, "STEP file is unexpectedly small"
    return data


@pytest.mark.asyncio
async def test_real_step_file_loads_to_geometry(real_step_file_bytes: bytes) -> None:
    """Stage 1 should parse real STEP content into non-empty geometry."""
    loader = StepLoaderService()
    geometry = await loader.process(real_step_file_bytes)

    assert len(geometry.vertices) > 0
    assert len(geometry.normals) == len(geometry.vertices)
    assert len(geometry.indices) >= 3
    assert geometry.metadata.get("solids_count", 0) >= 1
    assert "bounds" in geometry.metadata


@pytest.mark.asyncio
async def test_real_step_file_runs_full_pipeline_stages(real_step_file_bytes: bytes) -> None:
    """Real STEP file should pass through all four pipeline stages."""
    loader = StepLoaderService()
    extractor = PartsExtractorService()
    svg_generator = SvgGeneratorService()
    assembly_generator = AssemblyGeneratorService()

    geometry = await loader.process(real_step_file_bytes)
    parts = await extractor.process(geometry)
    drawings = await svg_generator.process(parts)
    steps = await assembly_generator.process(parts, drawings, preview_only=False)

    assert len(parts) > 0
    assert len(drawings) == len(parts)
    assert len(steps) > 0

    for step in steps:
        assert len(step.part_indices) > 0
        assert isinstance(step.title, str) and step.title
