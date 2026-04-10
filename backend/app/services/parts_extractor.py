"""Stage 2: Parts Extraction Service."""

import logging
from typing import List

from app.services.step_loader import PipelineStage
from app.models.schemas import Part, PartType, Geometry3D

logger = logging.getLogger(__name__)


class PartsExtractorService(PipelineStage):
    """
    Stage 2: Extract and classify parts from geometry.

    Input:  Geometry3D (from Stage 1)
    Output: Parts[] (with classification and deduplication)
    """

    def __init__(self) -> None:
        self.name = "PartsExtractorService"
        self.logger = logging.getLogger(__name__)

    async def validate_input(self, data: Geometry3D) -> bool:
        """Validate geometry has solids."""
        return len(data.vertices) > 0

    async def process(self, geometry: Geometry3D) -> List[Part]:
        """
        Extract parts from geometry and classify them.

        MOCK: Returns sample parts for testing infrastructure.
        """

        is_valid = await self.validate_input(geometry)
        if not is_valid:
            raise ValueError("Invalid geometry input")

        self.logger.info("Extracting and classifying parts...")

        # MOCK: Return sample parts
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

        self.logger.info(f"Extracted {len(parts)} unique parts")
        return parts
