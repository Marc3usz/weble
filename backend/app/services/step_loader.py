"""Stage 1: STEP Loading Service."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from app.models.schemas import Geometry3D
from app.core.exceptions import InvalidStepFileError, NoSolidsFoundError

logger = logging.getLogger(__name__)


class PipelineStage(ABC):
    """Base class for all pipeline stages."""

    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """Process input data and return output."""
        pass

    @abstractmethod
    async def validate_input(self, data: Any) -> bool:
        """Validate that input meets requirements."""
        pass


class StepLoaderService(PipelineStage):
    """
    Stage 1: Load STEP file and extract 3D geometry.

    Input:  STEP file content (bytes)
    Output: Geometry3D (vertices, normals, indices)
    """

    def __init__(self) -> None:
        self.name = "StepLoaderService"
        self.logger = logging.getLogger(__name__)

    async def validate_input(self, data: bytes) -> bool:
        """Validate that input is a valid STEP file."""
        if not isinstance(data, bytes):
            return False
        if len(data) < 100:  # Minimal STEP file size
            return False
        if not data.startswith(b"ISO-10303-21"):  # STEP file signature
            return False
        return True

    async def process(self, file_content: bytes) -> Geometry3D:
        """
        Load STEP file and extract geometry.

        This is a MOCK implementation that returns sample geometry.
        In Phase 1, we'll test the infrastructure without CadQuery.
        """

        # Validate input
        is_valid = await self.validate_input(file_content)
        if not is_valid:
            raise InvalidStepFileError("File is not a valid STEP file or too small")

        self.logger.info("Loading STEP file...")

        # MOCK: Return sample geometry for testing
        # In real implementation, this would use CadQuery to load the file
        try:
            # Simple cube geometry as mock data
            geometry = Geometry3D(
                vertices=[
                    [0, 0, 0],
                    [1, 0, 0],
                    [1, 1, 0],
                    [0, 1, 0],  # bottom
                    [0, 0, 1],
                    [1, 0, 1],
                    [1, 1, 1],
                    [0, 1, 1],  # top
                ],
                normals=[
                    [0, 0, -1],
                    [0, 0, -1],
                    [0, 0, -1],
                    [0, 0, -1],
                    [0, 0, 1],
                    [0, 0, 1],
                    [0, 0, 1],
                    [0, 0, 1],
                ],
                indices=[
                    # Bottom face
                    0,
                    1,
                    2,
                    0,
                    2,
                    3,
                    # Top face
                    4,
                    6,
                    5,
                    4,
                    7,
                    6,
                    # Sides
                    0,
                    4,
                    5,
                    0,
                    5,
                    1,
                    1,
                    5,
                    6,
                    1,
                    6,
                    2,
                    2,
                    6,
                    7,
                    2,
                    7,
                    3,
                    3,
                    7,
                    4,
                    3,
                    4,
                    0,
                ],
                metadata={
                    "solids_count": 1,
                    "bounds": {"min": [0, 0, 0], "max": [1, 1, 1]},
                    "total_triangles": 12,
                },
            )

            self.logger.info(f"Successfully loaded geometry: {len(geometry.vertices)} vertices")
            return geometry

        except Exception as e:
            self.logger.error(f"Failed to load STEP file: {e}")
            raise InvalidStepFileError(f"Failed to parse STEP file: {str(e)}")
