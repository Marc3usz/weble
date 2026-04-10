"""Stage 3: SVG Drawing Generation Service."""

import logging
from typing import List

from app.services.step_loader import PipelineStage
from app.models.schemas import Part, SvgDrawing

logger = logging.getLogger(__name__)


class SvgGeneratorService(PipelineStage):
    """
    Stage 3: Generate 2D technical drawings for parts.

    Input:  Parts[] (from Stage 2)
    Output: SvgDrawing[] (SVG content for each part)
    """

    def __init__(self) -> None:
        self.name = "SvgGeneratorService"
        self.logger = logging.getLogger(__name__)

    async def validate_input(self, data: List[Part]) -> bool:
        """Validate parts list."""
        return isinstance(data, list) and len(data) > 0

    async def process(self, parts: List[Part]) -> List[SvgDrawing]:
        """
        Generate SVG drawings for parts.

        MOCK: Returns sample SVG for testing infrastructure.
        """

        is_valid = await self.validate_input(parts)
        if not is_valid:
            raise ValueError("Invalid parts input")

        self.logger.info("Generating SVG drawings...")

        # MOCK: Generate simple SVG for each part
        drawings = []
        for part in parts:
            # Simple SVG rectangle as mock
            svg_content = f"""<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="10" width="180" height="180" stroke="black" fill="white" stroke-width="2"/>
  <text x="100" y="100" text-anchor="middle" font-size="14">Part {part.id}</text>
  <text x="100" y="120" text-anchor="middle" font-size="12" fill="gray">Volume: {part.volume:.1f}</text>
  {"<text x='100' y='140' text-anchor='middle' font-size='14' font-weight='bold'>×" + str(part.quantity) + "</text>" if part.quantity > 1 else ""}
</svg>"""

            drawings.append(
                SvgDrawing(
                    part_id=part.id,
                    svg_content=svg_content,
                    quantity_label=f"×{part.quantity}" if part.quantity > 1 else "",
                    metadata={},
                )
            )

        self.logger.info(f"Generated {len(drawings)} SVG drawings")
        return drawings
