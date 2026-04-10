"""Pytest configuration and shared fixtures."""

import pytest
import pytest_asyncio
from app.container import ServiceContainer
from app.db.memory import InMemoryDatabase
from app.services.step_loader import StepLoaderService
from app.services.parts_extractor import PartsExtractorService
from app.services.svg_generator import SvgGeneratorService
from app.services.assembly_generator import AssemblyGeneratorService
from app.services.progress_tracker import ProgressTracker


@pytest_asyncio.fixture
async def memory_db():
    """Create an in-memory database for testing."""
    db = InMemoryDatabase()
    await db.initialize()
    return db


@pytest_asyncio.fixture
async def progress_tracker():
    """Create a progress tracker for testing."""
    return ProgressTracker()


@pytest_asyncio.fixture
async def service_container(memory_db, progress_tracker):
    """Create a service container with all dependencies."""
    container = ServiceContainer()
    container._db = memory_db
    container._progress_tracker = progress_tracker
    container._step_loader = StepLoaderService()
    container._parts_extractor = PartsExtractorService()
    container._svg_generator = SvgGeneratorService()
    container._assembly_generator = AssemblyGeneratorService()
    return container


@pytest.fixture
def valid_step_file_content():
    """Create a valid minimal STEP file content (just header)."""
    # Minimal STEP file with ISO-10303-21 header
    content = (
        b"ISO-10303-21;\n"
        b"HEADER;\n"
        b"FILE_DESCRIPTION(('Test STEP File'),\n"
        b"'2;1');\n"
        b"FILE_NAME('test.step',\n"
        b"2024-01-01T00:00:00,(''),(''),\n"
        b"'',\n"
        b"'',\n"
        b"'');\n"
        b"FILE_SCHEMA(('AP214'));\n"
        b"ENDSEC;\n"
        b"DATA;\n"
        b"ENDSEC;\n"
        b"END-ISO-10303-21;\n"
    )
    return content


@pytest.fixture
def invalid_step_file_content():
    """Create an invalid STEP file content."""
    return b"This is not a valid STEP file"


@pytest.fixture
def too_small_file_content():
    """Create a file that's too small to be valid."""
    return b"ISO-10303-21"
