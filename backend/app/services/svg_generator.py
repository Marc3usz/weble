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

        Uses part dimensions to create a simple isometric-style technical SVG.
        """

        is_valid = await self.validate_input(parts)
        if not is_valid:
            raise ValueError("Invalid parts input")

        self.logger.info("Generating SVG drawings...")

        drawings = []
        for part in parts:
            width = max(float(part.dimensions.get("width", 1.0)), 1.0)
            height = max(float(part.dimensions.get("height", 1.0)), 1.0)
            depth = max(float(part.dimensions.get("depth", 1.0)), 1.0)

            scale = 120.0 / max(width, height, depth)
            w = width * scale
            h = height * scale
            d = depth * scale * 0.6

            origin_x = 60.0
            origin_y = 150.0

            front_left = (origin_x, origin_y)
            front_right = (origin_x + w, origin_y)
            top_left = (origin_x + d, origin_y - d)
            top_right = (origin_x + w + d, origin_y - d)
            back_top_left = (origin_x + d, origin_y - h - d)
            back_top_right = (origin_x + w + d, origin_y - h - d)
            front_top_left = (origin_x, origin_y - h)
            front_top_right = (origin_x + w, origin_y - h)

            svg_content = f"""<svg width="320" height="220" xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="320" height="220" fill="white"/>
  <polygon points="{top_left[0]:.1f},{top_left[1]:.1f} {top_right[0]:.1f},{top_right[1]:.1f} {back_top_right[0]:.1f},{back_top_right[1]:.1f} {back_top_left[0]:.1f},{back_top_left[1]:.1f}" fill="#f5f7fb" stroke="#111" stroke-width="1.2"/>
  <polygon points="{front_left[0]:.1f},{front_left[1]:.1f} {front_right[0]:.1f},{front_right[1]:.1f} {front_top_right[0]:.1f},{front_top_right[1]:.1f} {front_top_left[0]:.1f},{front_top_left[1]:.1f}" fill="#ffffff" stroke="#111" stroke-width="1.2"/>
  <polygon points="{front_right[0]:.1f},{front_right[1]:.1f} {top_right[0]:.1f},{top_right[1]:.1f} {back_top_right[0]:.1f},{back_top_right[1]:.1f} {front_top_right[0]:.1f},{front_top_right[1]:.1f}" fill="#e9edf5" stroke="#111" stroke-width="1.2"/>

  <text x="20" y="24" font-size="14" font-family="Arial, sans-serif" font-weight="700">Part {part.id}</text>
  <text x="20" y="44" font-size="12" font-family="Arial, sans-serif" fill="#444">Type: {part.part_type.value}</text>
  <text x="20" y="62" font-size="12" font-family="Arial, sans-serif" fill="#444">Volume: {part.volume:.1f}</text>
  <text x="20" y="80" font-size="12" font-family="Arial, sans-serif" fill="#444">W x H x D: {width:.1f} x {height:.1f} x {depth:.1f}</text>
  {"<text x='20' y='100' font-size='16' font-family='Arial, sans-serif' font-weight='700'>×" + str(part.quantity) + "</text>" if part.quantity > 1 else ""}
</svg>"""

            drawings.append(
                SvgDrawing(
                    part_id=part.id,
                    svg_content=svg_content,
                    quantity_label=f"×{part.quantity}" if part.quantity > 1 else "",
                    metadata={
                        "projection": "isometric-ish",
                        "dimensions": {"width": width, "height": height, "depth": depth},
                    },
                )
            )

        self.logger.info(f"Generated {len(drawings)} SVG drawings")
        return drawings
