"""Stage 3: SVG Drawing Generation Service - Phase 2 with HLR."""

import logging
import math
from typing import List, Dict, Tuple

from app.services.step_loader import PipelineStage
from app.models.schemas import Part, SvgDrawing

logger = logging.getLogger(__name__)


class TechnicalDrawing:
    """Helper class for engineering drawing calculations."""

    @staticmethod
    def calculate_canvas_size(
        width: float, height: float, depth: float
    ) -> Tuple[float, float, float]:
        """
        Calculate appropriate canvas size and scale for technical drawing.

        Uses dynamic sizing based on part dimensions to avoid crowding.

        Returns:
            (canvas_width, canvas_height, scale)
        """
        max_dim = max(width, height, depth)
        # Scale to fit in a reasonable canvas (150-400px for main geometry)
        scale = 250.0 / max(max_dim, 1.0)

        # Add margins for annotations
        margin = 40
        canvas_width = width * scale + 2 * margin
        canvas_height = max(height * scale + depth * scale * 0.5, 200) + 2 * margin

        return canvas_width, canvas_height, scale

    @staticmethod
    def project_orthographic_front(
        width: float, height: float, scale: float, offset_x: float, offset_y: float
    ) -> Dict[str, Tuple[float, float]]:
        """
        Generate orthographic front view projection.

        Standard engineering drawing: rectangular face showing width x height.
        """
        w = width * scale
        h = height * scale

        return {
            "bottom_left": (offset_x, offset_y),
            "bottom_right": (offset_x + w, offset_y),
            "top_right": (offset_x + w, offset_y - h),
            "top_left": (offset_x, offset_y - h),
        }

    @staticmethod
    def project_orthographic_top(
        width: float, depth: float, scale: float, offset_x: float, offset_y: float
    ) -> Dict[str, Tuple[float, float]]:
        """
        Generate orthographic top view projection (plan view).

        Shows width x depth, positioned below front view.
        """
        w = width * scale
        d = depth * scale

        return {
            "back_left": (offset_x, offset_y),
            "back_right": (offset_x + w, offset_y),
            "front_right": (offset_x + w, offset_y + d),
            "front_left": (offset_x, offset_y + d),
        }

    @staticmethod
    def draw_dimension_line(
        x1: float, y1: float, x2: float, y2: float, label: str, dimension_height: float = 20
    ) -> str:
        """
        Draw a dimension line with measurement label (CAD-style).

        Includes leader lines, endpoints, and text annotation.
        """
        # Calculate dimension line position
        extension = 15
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2

        svg = f"""    <!-- Dimension: {label} -->
    <line x1="{x1}" y1="{y1 - extension}" x2="{x1}" y2="{y1}" stroke="#666" stroke-width="0.5"/>
    <line x1="{x2}" y1="{y2 - extension}" x2="{x2}" y2="{y2}" stroke="#666" stroke-width="0.5"/>
    <line x1="{x1}" y1="{y1 - extension}" x2="{x2}" y2="{y2 - extension}" stroke="#666" stroke-width="0.8"/>
    <!-- Arrowheads -->
    <polygon points="{x1},{y1 - extension} {x1 - 3},{y1 - extension + 4} {x1 + 3},{y1 - extension + 4}" fill="#666"/>
    <polygon points="{x2},{y2 - extension} {x2 - 3},{y2 - extension + 4} {x2 + 3},{y2 - extension + 4}" fill="#666"/>
    <!-- Dimension text -->
    <text x="{mid_x}" y="{y1 - extension - 5}" font-size="10" font-family="Arial, sans-serif" 
          text-anchor="middle" fill="#333">{label}</text>
"""
        return svg


class SvgGeneratorService(PipelineStage):
    """
    Stage 3: Generate 2D technical drawings for parts (Phase 2 with HLR).

    Input:  Parts[] (from Stage 2)
    Output: SvgDrawing[] (Engineering drawing SVG content)

    Phase 2 Features:
    - Orthographic multi-view drawings (front, top, isometric)
    - HLR-inspired hidden line visualization
    - Engineering dimension annotations
    - Professional technical drawing format
    - Dynamic canvas sizing
    - Part classification indicators
    """

    def __init__(self) -> None:
        self.name = "SvgGeneratorService"
        self.logger = logging.getLogger(__name__)
        self.drawing_helper = TechnicalDrawing()

    async def validate_input(self, data: List[Part]) -> bool:
        """Validate parts list."""
        return isinstance(data, list) and len(data) > 0

    async def process(self, parts: List[Part]) -> List[SvgDrawing]:
        """
        Generate technical drawings for parts using Phase 2 HLR approach.

        Each drawing includes:
        - Orthographic front view with dimensions
        - Top view (plan)
        - Isometric view with hidden line rendering
        - Material and quantity annotations
        """

        is_valid = await self.validate_input(parts)
        if not is_valid:
            raise ValueError("Invalid parts input")

        self.logger.info("Generating Phase 2 engineering drawings with HLR...")

        drawings = []
        for part in parts:
            svg_content = self._generate_technical_drawing(part)

            drawings.append(
                SvgDrawing(
                    part_id=part.id,
                    svg_content=svg_content,
                    quantity_label=f"×{part.quantity}" if part.quantity > 1 else "",
                    metadata={
                        "projection": "orthographic_multi_view_hlr",
                        "includes": ["front_view", "top_view", "isometric"],
                        "dimensions": {
                            "width": float(part.dimensions.get("width", 0)),
                            "height": float(part.dimensions.get("height", 0)),
                            "depth": float(part.dimensions.get("depth", 0)),
                        },
                        "part_type": part.part_type.value,
                        "quantity": part.quantity,
                        "volume": part.volume,
                    },
                )
            )

        self.logger.info(f"Generated {len(drawings)} Phase 2 engineering drawings")
        return drawings

    def _generate_technical_drawing(self, part: Part) -> str:
        """Generate complete technical drawing for a part."""
        w = max(float(part.dimensions.get("width", 1.0)), 1.0)
        h = max(float(part.dimensions.get("height", 1.0)), 1.0)
        d = max(float(part.dimensions.get("depth", 1.0)), 1.0)

        # Calculate canvas size dynamically
        canvas_w, canvas_h, scale = self.drawing_helper.calculate_canvas_size(w, h, d)
        canvas_w = max(canvas_w, 400)
        canvas_h = max(canvas_h, 350)

        margin = 30
        view_margin = 20

        # Generate views
        front_view = self._draw_front_view(w, h, scale, margin, margin + 40, part)
        top_view = self._draw_top_view(w, d, scale, margin, margin + h * scale + 80, part)
        iso_view = self._draw_isometric_hlr(
            w, h, d, scale, margin + w * scale + 60, margin + 40, part
        )

        # Annotations
        annotations = self._generate_annotations(part, canvas_w, canvas_h)

        svg = f"""<svg width="{canvas_w:.0f}" height="{canvas_h:.0f}" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <defs>
    <style>
      .title {{ font-size: 16px; font-weight: bold; font-family: Arial, sans-serif; }}
      .label {{ font-size: 11px; font-family: Arial, sans-serif; fill: #333; }}
      .dimension {{ font-size: 10px; font-family: Arial, sans-serif; fill: #555; }}
      .view-label {{ font-size: 12px; font-weight: bold; font-family: Arial, sans-serif; fill: #000; }}
      .metadata {{ font-size: 10px; font-family: monospace; fill: #666; }}
    </style>
  </defs>
  
  <rect width="{canvas_w:.0f}" height="{canvas_h:.0f}" fill="white" stroke="#ddd" stroke-width="1"/>
  
  <!-- Title block -->
  <text x="{margin}" y="25" class="title">Part {part.id} - Technical Drawing (Phase 2 HLR)</text>
  
  <!-- Front View (Primary) -->
  <g id="front-view">
    <text x="{margin}" y="{margin + 30}" class="view-label">FRONT VIEW</text>
{front_view}
  </g>
  
  <!-- Top View (Plan) -->
  <g id="top-view">
    <text x="{margin}" y="{margin + h * scale + 65}" class="view-label">TOP VIEW (PLAN)</text>
{top_view}
  </g>
  
  <!-- Isometric View with HLR -->
  <g id="isometric-view">
    <text x="{margin + w * scale + 60}" y="{margin + 30}" class="view-label">ISOMETRIC (HLR)</text>
{iso_view}
  </g>
  
  <!-- Material & Metadata Block -->
{annotations}
</svg>"""

        return svg

    def _draw_front_view(
        self,
        width: float,
        height: float,
        scale: float,
        offset_x: float,
        offset_y: float,
        part: Part,
    ) -> str:
        """Draw orthographic front view with dimensions and HLR."""
        proj = self.drawing_helper.project_orthographic_front(
            width, height, scale, offset_x, offset_y
        )

        w_scaled = width * scale
        h_scaled = height * scale

        # Main rectangle (solid edges - visible faces)
        svg = f"""    <rect x="{proj["bottom_left"][0]:.1f}" y="{proj["top_left"][1]:.1f}" 
         width="{w_scaled:.1f}" height="{h_scaled:.1f}" 
         fill="none" stroke="#111" stroke-width="1.5"/>
    
    <!-- Center lines (hidden line indicators) -->
    <line x1="{offset_x + w_scaled / 2:.1f}" y1="{offset_y:.1f}" 
          x2="{offset_x + w_scaled / 2:.1f}" y2="{offset_y - h_scaled:.1f}" 
          stroke="#999" stroke-width="0.5" stroke-dasharray="3,3"/>
    <line x1="{offset_x:.1f}" y1="{offset_y - h_scaled / 2:.1f}" 
          x2="{offset_x + w_scaled:.1f}" y2="{offset_y - h_scaled / 2:.1f}" 
          stroke="#999" stroke-width="0.5" stroke-dasharray="3,3"/>
    
    <!-- Dimension lines -->
    <line x1="{offset_x:.1f}" y1="{offset_y + 15:.1f}" 
          x2="{offset_x + w_scaled:.1f}" y2="{offset_y + 15:.1f}" 
          stroke="#666" stroke-width="0.8"/>
    <text x="{offset_x + w_scaled / 2:.1f}" y="{offset_y + 28:.1f}" 
          text-anchor="middle" class="dimension">{width:.1f}</text>
    
    <line x1="{offset_x - 15:.1f}" y1="{offset_y:.1f}" 
          x2="{offset_x - 15:.1f}" y2="{offset_y - h_scaled:.1f}" 
          stroke="#666" stroke-width="0.8"/>
    <text x="{offset_x - 30:.1f}" y="{offset_y - h_scaled / 2:.1f}" 
          text-anchor="middle" class="dimension" transform="rotate(-90 {offset_x - 30:.1f} {offset_y - h_scaled / 2:.1f})">{height:.1f}</text>
"""
        return svg

    def _draw_top_view(
        self, width: float, depth: float, scale: float, offset_x: float, offset_y: float, part: Part
    ) -> str:
        """Draw orthographic top view (plan view) with dimensions."""
        proj = self.drawing_helper.project_orthographic_top(width, depth, scale, offset_x, offset_y)

        w_scaled = width * scale
        d_scaled = depth * scale

        svg = f"""    <rect x="{offset_x:.1f}" y="{offset_y:.1f}" 
         width="{w_scaled:.1f}" height="{d_scaled:.1f}" 
         fill="none" stroke="#111" stroke-width="1.5"/>
    
    <!-- Dashed lines indicating depth -->
    <line x1="{offset_x + w_scaled / 2:.1f}" y1="{offset_y:.1f}" 
          x2="{offset_x + w_scaled / 2:.1f}" y2="{offset_y + d_scaled:.1f}" 
          stroke="#999" stroke-width="0.5" stroke-dasharray="3,3"/>
    
    <!-- Dimension -->
    <text x="{offset_x + w_scaled / 2:.1f}" y="{offset_y + d_scaled + 15:.1f}" 
          text-anchor="middle" class="dimension">{width:.1f} × {depth:.1f}</text>
"""
        return svg

    def _draw_isometric_hlr(
        self,
        width: float,
        height: float,
        depth: float,
        scale: float,
        offset_x: float,
        offset_y: float,
        part: Part,
    ) -> str:
        """
        Draw isometric view with HLR (hidden line removal) styling.

        Uses dashed lines for hidden edges, solid for visible edges.
        Three faces shown: front, top, and right side.
        """
        # Scale dimensions
        w = width * scale
        h = height * scale
        d = depth * scale * 0.5  # Depth foreshortened for isometric

        # Define vertices for isometric box
        origin_x = offset_x
        origin_y = offset_y

        # Visible front face vertices
        fl = (origin_x, origin_y)  # front-left
        fr = (origin_x + w, origin_y)  # front-right
        ftl = (origin_x, origin_y - h)  # front-top-left
        ftr = (origin_x + w, origin_y - h)  # front-top-right

        # Top face vertices (receding)
        tl = (origin_x + d, origin_y - d)  # top-left
        tr = (origin_x + w + d, origin_y - d)  # top-right

        # Back vertices (hidden)
        btl = (origin_x + d, origin_y - h - d)  # back-top-left
        btr = (origin_x + w + d, origin_y - h - d)  # back-top-right

        # HLR visualization: use colors and dashes to show depth
        svg = f"""    <!-- Top face (HLR: slightly hidden) -->
    <polygon points="{tl[0]:.1f},{tl[1]:.1f} {tr[0]:.1f},{tr[1]:.1f} {btr[0]:.1f},{btr[1]:.1f} {btl[0]:.1f},{btl[1]:.1f}" 
             fill="#e8eef7" stroke="#333" stroke-width="1"/>
    
    <!-- Front face (HLR: fully visible) -->
    <polygon points="{fl[0]:.1f},{fl[1]:.1f} {fr[0]:.1f},{fr[1]:.1f} {ftr[0]:.1f},{ftr[1]:.1f} {ftl[0]:.1f},{ftl[1]:.1f}" 
             fill="#ffffff" stroke="#000" stroke-width="1.5"/>
    
    <!-- Right face (HLR: partially visible) -->
    <polygon points="{fr[0]:.1f},{fr[1]:.1f} {tr[0]:.1f},{tr[1]:.1f} {btr[0]:.1f},{btr[1]:.1f} {ftr[0]:.1f},{ftr[1]:.1f}" 
             fill="#d9dfe8" stroke="#333" stroke-width="1"/>
    
    <!-- Hidden edges (dashed) -->
    <line x1="{tl[0]:.1f}" y1="{tl[1]:.1f}" x2="{btl[0]:.1f}" y2="{btl[1]:.1f}" 
          stroke="#999" stroke-width="0.8" stroke-dasharray="2,2"/>
    <line x1="{tr[0]:.1f}" y1="{tr[1]:.1f}" x2="{btr[0]:.1f}" y2="{btr[1]:.1f}" 
          stroke="#999" stroke-width="0.8" stroke-dasharray="2,2"/>
    <line x1="{ftl[0]:.1f}" y1="{ftl[1]:.1f}" x2="{btl[0]:.1f}" y2="{btl[1]:.1f}" 
          stroke="#999" stroke-width="0.8" stroke-dasharray="2,2"/>
    <line x1="{btl[0]:.1f}" y1="{btl[1]:.1f}" x2="{btr[0]:.1f}" y2="{btr[1]:.1f}" 
          stroke="#999" stroke-width="0.8" stroke-dasharray="2,2"/>
    
    <!-- Dimension annotation -->
    <text x="{origin_x + w / 2:.1f}" y="{origin_y + 15:.1f}" 
          text-anchor="middle" class="dimension" fill="#333">{width:.0f}mm</text>
"""
        return svg

    def _generate_annotations(self, part: Part, canvas_w: float, canvas_h: float) -> str:
        """Generate material block and metadata annotations."""
        metadata_y = canvas_h - 120

        # Part classification color
        type_color = {
            "panel": "#4a90e2",
            "hardware": "#f5a623",
            "fastener": "#d0021b",
            "structural": "#7ed321",
            "other": "#999999",
        }.get(part.part_type.value, "#999999")

        svg = f"""  <!-- Material & Specification Block -->
  <g id="metadata-block">
    <rect x="20" y="{metadata_y:.0f}" width="200" height="100" 
          fill="#f9f9f9" stroke="#ccc" stroke-width="1"/>
    
    <text x="30" y="{metadata_y + 18:.0f}" class="label" font-weight="bold">PART: {part.id}</text>
    <text x="30" y="{metadata_y + 35:.0f}" class="label">Type: {part.part_type.value}</text>
    
    <!-- Type indicator -->
    <circle cx="200" cy="{metadata_y + 28:.0f}" r="4" fill="{type_color}"/>
    
    <text x="30" y="{metadata_y + 52:.0f}" class="label">Volume: {part.volume:.1f} cm³</text>
    <text x="30" y="{metadata_y + 69:.0f}" class="label">Surface: {part.surface_area:.1f} cm²</text>
    
    {f'<text x="30" y="{metadata_y + 86:.0f}" class="label" font-weight="bold" fill="{type_color}">QTY: {part.quantity}</text>' if part.quantity > 1 else ""}
  </g>
  
  <!-- Drawing Info -->
  <g id="drawing-info">
    <text x="{canvas_w - 200:.0f}" y="{metadata_y + 18:.0f}" class="metadata" font-size="9">Projection: Orthographic + Isometric HLR</text>
    <text x="{canvas_w - 200:.0f}" y="{metadata_y + 32:.0f}" class="metadata" font-size="9">Scale: Dynamic (Part-fitted)</text>
    <text x="{canvas_w - 200:.0f}" y="{metadata_y + 46:.0f}" class="metadata" font-size="9">Standard: ISO/ASME-like</text>
    <text x="{canvas_w - 200:.0f}" y="{metadata_y + 60:.0f}" class="metadata" font-size="9">Phase: 2 (HLR Enhanced)</text>
    <text x="{canvas_w - 200:.0f}" y="{metadata_y + 74:.0f}" class="metadata" font-size="9">Group: {part.group_id}</text>
  </g>
"""

        return svg
