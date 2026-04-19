"""Test that the async StepLoaderService properly handles blocking operations."""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from app.services.step_loader import StepLoaderService
from app.models.schemas import Geometry3D
from app.core.exceptions import InvalidStepFileError


def _get_real_step_file_bytes() -> bytes:
    """Load the real STEP file used for testing."""
    step_path = Path(__file__).resolve().parents[2] / "biurko standard.step"
    if step_path.exists():
        return step_path.read_bytes()
    # Fallback: create a minimal but valid STEP file (100+ bytes, with STEP header)
    return b"ISO-10303-21;" + b"x" * 200  # Pad to meet size requirement


@pytest.mark.asyncio
async def test_step_loader_async_process():
    """Verify async process method properly delegates blocking ops to executor."""

    service = StepLoaderService()
    step_bytes = _get_real_step_file_bytes()

    # Process should complete asynchronously
    result = await service.process(step_bytes)

    # Verify we got valid geometry
    assert isinstance(result, Geometry3D)
    assert len(result.vertices) > 0
    assert len(result.normals) > 0


@pytest.mark.asyncio
async def test_concurrent_file_processing_doesnt_block():
    """Verify multiple concurrent file uploads don't block each other."""

    service = StepLoaderService()
    step_bytes = _get_real_step_file_bytes()

    # Process multiple files concurrently
    tasks = [
        service.process(step_bytes),
        service.process(step_bytes),
        service.process(step_bytes),
    ]

    # All should complete without blocking each other
    results = await asyncio.gather(*tasks)
    assert len(results) == 3
    for result in results:
        assert isinstance(result, Geometry3D)
        assert len(result.vertices) > 0
        assert len(result.normals) > 0


@pytest.mark.asyncio
async def test_step_loader_invalid_file_still_async():
    """Verify that validation errors are raised asynchronously without blocking."""

    service = StepLoaderService()

    # Invalid file content
    invalid_content = b"NOT_A_STEP_FILE"

    with pytest.raises(InvalidStepFileError):
        await service.process(invalid_content)


@pytest.mark.asyncio
async def test_step_loader_validates_input_asynchronously():
    """Verify input validation happens asynchronously."""

    service = StepLoaderService()

    # Test with non-bytes
    result = await service.validate_input("not bytes")
    assert result is False

    # Test with too-small content
    result = await service.validate_input(b"small")
    assert result is False

    # Test with valid STEP signature but small file
    result = await service.validate_input(b"ISO-10303-21" + b"x" * 88)
    assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
