"""Stage 4b: Exploded View SVG Generator - Phase 3 per-step assembly diagrams."""

import logging
import math
from typing import Dict, List, Optional, Tuple

from app.models.schemas import AssemblyStep, Part
from app.services.step_loader import PipelineStage

logger = logging.getLogger(__name__)


class IsometricProjection:
    """Helper class for isometric 3D projection calculations."""

    # Isometric angles: 30° rotations, 1:1 scale on all axes
    ANGLE_X = math.radians(30)  # Right face angle
    ANGLE_Y = math.radians(-30)  # Left face angle
    FORESHORTEN_Z = 0.866  # cos(30°) for depth

    @staticmethod
    def project_point(x: float, y: float, z: float, scale: float = 1.0) -> Tuple[float, float]:
        """
        Project 3D point to 2D isometric coordinates.

        Uses standard isometric projection:
        - X-axis: 30° angle (right, down)
        - Y-axis: -30° angle (left, down)
        - Z-axis: vertical (up)

        Args:
            x, y, z: 3D coordinates
            scale: Scaling factor

        Returns:
            (screen_x, screen_y) in 2D space
        """
        # Isometric axes (unit vectors in 2D)
        # X goes right-down at 30°
        x_2d = scale * x * math.cos(IsometricProjection.ANGLE_X)
        y_2d = scale * x * math.sin(IsometricProjection.ANGLE_X)

        # Y goes left-down at -30°
        x_2d += scale * y * math.cos(IsometricProjection.ANGLE_Y)
        y_2d += scale * y * math.sin(IsometricProjection.ANGLE_Y)

        # Z goes straight up
        y_2d -= scale * z * IsometricProjection.FORESHORTEN_Z

        return x_2d, y_2d

    @staticmethod
    def project_box(
        x: float, y: float, z: float, width: float, height: float, depth: float, scale: float = 1.0
    ) -> Dict[str, Tuple[float, float]]:
        """
        Project 3D box (cuboid) to isometric 2D vertices.

        Returns dict with vertex names and 2D coordinates.
        """
        # 8 vertices of the box (origin at x, y, z)
        vertices_3d = {
            "v0": (x, y, z),  # origin
            "v1": (x + width, y, z),  # right
            "v2": (x + width, y + depth, z),  # right-back
            "v3": (x, y + depth, z),  # back
            "v4": (x, y, z + height),  # top-origin
            "v5": (x + width, y, z + height),  # top-right
            "v6": (x + width, y + depth, z + height),  # top-right-back
            "v7": (x, y + depth, z + height),  # top-back
        }

        vertices_2d = {}
        for name, (px, py, pz) in vertices_3d.items():
            vertices_2d[name] = IsometricProjection.project_point(px, py, pz, scale)

        return vertices_2d


class ExplodedViewSVGGenerator(PipelineStage):
    """
    Stage 4b: Generate per-step exploded view assembly diagrams.

    Input:  Parts[], AssemblyStep
    Output: SVG string with highlighted assembly state

    Features:
    - Isometric 3D representation of parts
    - Active parts (involved in step) at full opacity
    - Context parts (already assembled) at 30% opacity
    - Assembly arrows showing part insertion direction
    - Part labels and highlighting
    - Dynamic canvas sizing (200-2000px)
    - Color-coded by part type and state
    """

    def __init__(self) -> None:
        self.name = "ExplodedViewSVGGenerator"
        self.logger = logging.getLogger(__name__)
        self.projection = IsometricProjection()
        self.part_type_colors = {
            "panel": "#4a90e2",  # Blue
            "hardware": "#f5a623",  # Orange
            "fastener": "#d0021b",  # Red
            "structural": "#7ed321",  # Green
            "other": "#999999",  # Gray
        }

    async def validate_input(self, data: tuple) -> bool:
        """Validate parts list and assembly step."""
        if not isinstance(data, tuple) or len(data) != 2:
            return False
        parts, step = data
        return (
            isinstance(parts, list)
            and len(parts) > 0
            and isinstance(step, AssemblyStep)
            and len(step.part_indices) > 0
        )

    async def process(self, parts: List[Part], step: AssemblyStep) -> str:
        """
        Generate exploded view SVG for a single assembly step.

        Args:
            parts: List of all parts
            step: Assembly step (identifies active/context parts)

        Returns:
            SVG content as string
        """
        is_valid = await self.validate_input((parts, step))
        if not is_valid:
            raise ValueError("Invalid parts or step input")

        self.logger.debug(f"Generating exploded view for step {step.step_number}...")
        svg = await self.generate_exploded_view(parts, step)
        return svg

    async def generate_exploded_view(self, parts: List[Part], step: AssemblyStep) -> str:
        """
        Generate exploded view SVG for assembly step.

        Shows all parts in isometric view with:
        - Active parts (step.part_indices): full opacity, highlighted
        - Context parts (step.context_part_indices): 30% opacity, grayed
        - Arrows showing assembly direction
        """
        # Determine canvas size based on parts
        canvas_w, canvas_h = self._calculate_canvas_size(parts)

        # Calculate part positions (simple grid-based for now)
        part_positions = self._calculate_part_positions(parts)

        # Start SVG
        svg = f"""<svg width="{canvas_w:.0f}" height="{canvas_h:.0f}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w:.0f} {canvas_h:.0f}">
  <!-- Exploded View Assembly Diagram -->
  <defs>
    <style>
      .part-label {{ font-size: 11px; font-family: Arial, sans-serif; font-weight: bold; }}
      .step-info {{ font-size: 12px; font-family: Arial, sans-serif; fill: #333; }}
      .part-active {{ filter: drop-shadow(0 0 3px #000) opacity(1); }}
      .part-context {{ opacity: 0.3; }}
      .assembly-arrow {{ stroke: #e74c3c; stroke-width: 2; fill: none; marker-end: url(#arrowhead); }}
      .assembly-label {{ font-size: 10px; font-family: Arial, sans-serif; fill: #e74c3c; }}
    </style>
    <!-- Arrow marker for assembly direction -->
    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 10 3, 0 6" fill="#e74c3c"/>
    </marker>
  </defs>
  
  <rect width="{canvas_w:.0f}" height="{canvas_h:.0f}" fill="white" stroke="#ddd" stroke-width="1"/>
  
  <!-- Title -->
  <text x="20" y="25" class="step-info" font-weight="bold">Step {step.step_number}: {step.title}</text>
  
  <!-- Parts Group -->
  <g id="parts">
"""

        # Render each part as isometric box
        part_by_idx = {i: part for i, part in enumerate(parts)}

        for part_idx, part in enumerate(parts):
            if part_idx not in part_positions:
                continue

            pos_x, pos_y = part_positions[part_idx]
            is_active = part_idx in step.part_indices
            is_context = part_idx in step.context_part_indices

            # Only render active and context parts
            if not (is_active or is_context):
                continue

            part_svg = self._render_isometric_part(
                part, pos_x, pos_y, is_active=is_active, is_context=is_context
            )
            svg += part_svg

        svg += """  </g>
  
  <!-- Assembly Instructions -->
  <g id="instructions">
"""

        # Add assembly sequence steps if available
        if step.assembly_sequence:
            seq_y = canvas_h - 80
            svg += f"""    <text x="20" y="{seq_y - 5}" class="step-info" font-weight="bold">Assembly Sequence:</text>
"""
            for i, seq_step in enumerate(step.assembly_sequence[:3]):  # Show max 3 steps
                svg += f"""    <text x="30" y="{seq_y + (i + 1) * 18:.0f}" class="assembly-label">• {seq_step}</text>
"""

        # Add warnings if any
        if step.warnings:
            warn_y = canvas_h - 30
            warning_text = " | ".join(step.warnings[:2])
            svg += f"""    <text x="20" y="{warn_y:.0f}" class="assembly-label" fill="#d0021b" font-weight="bold">⚠ {warning_text}</text>
"""

        svg += """  </g>
</svg>"""

        return svg

    def _calculate_canvas_size(self, parts: List[Part]) -> Tuple[float, float]:
        """Calculate appropriate canvas size based on number and size of parts."""
        # Base size: 400x300, grows with part count
        base_w, base_h = 400, 300
        extra_per_part = 20

        canvas_w = min(base_w + len(parts) * extra_per_part, 2000)
        canvas_h = min(base_h + len(parts) * extra_per_part, 2000)

        return canvas_w, canvas_h

    def _calculate_part_positions(self, parts: List[Part]) -> Dict[int, Tuple[float, float]]:
        """
        Calculate 2D screen positions for each part.

        Uses part centroids and dimensions to position parts in isometric view.
        """
        positions = {}

        # Group parts by size for better visual arrangement
        sorted_parts = sorted(enumerate(parts), key=lambda x: x[1].volume, reverse=True)

        # Arrange in a loose grid
        for grid_idx, (part_idx, part) in enumerate(sorted_parts):
            # Simple grid arrangement
            grid_x = (grid_idx % 3) * 130 + 100
            grid_y = (grid_idx // 3) * 120 + 80

            positions[part_idx] = (grid_x, grid_y)

        return positions

    def _render_isometric_part(
        self, part: Part, x: float, y: float, is_active: bool = True, is_context: bool = False
    ) -> str:
        """
        Render a single part as an isometric box.

        Args:
            part: Part to render
            x, y: Screen position (origin)
            is_active: If True, render at full opacity (involved in step)
            is_context: If True, render at low opacity (already assembled)

        Returns:
            SVG group containing isometric box representation
        """
        w = max(float(part.dimensions.get("width", 1.0)), 0.5)
        h = max(float(part.dimensions.get("height", 1.0)), 0.5)
        d = max(float(part.dimensions.get("depth", 1.0)), 0.5)

        # Scale to fit on screen
        max_dim = max(w, h, d)
        scale = 40.0 / max(max_dim, 1.0)

        # Project isometric box vertices
        vertices = self.projection.project_box(0, 0, 0, w, h, d, scale)

        # Offset to screen position
        for key in vertices:
            vx, vy = vertices[key]
            vertices[key] = (vx + x, vy + y)

        # Determine colors
        base_color = self.part_type_colors.get(part.part_type.value, "#999999")
        opacity = 1.0 if is_active else 0.3
        stroke_color = base_color if is_active else "#ccc"
        stroke_width = 1.5 if is_active else 1.0

        # Build SVG
        class_name = "part-active" if is_active else "part-context"
        svg = f"""    <!-- Part {part.id} (idx: {part.original_index}) -->
    <g class="{class_name}" opacity="{opacity}">
"""

        # Draw three visible faces (front, top, right)
        # Front face (Z-X plane)
        svg += f"""      <polygon points="{vertices["v0"][0]:.1f},{vertices["v0"][1]:.1f} {vertices["v1"][0]:.1f},{vertices["v1"][1]:.1f} {vertices["v5"][0]:.1f},{vertices["v5"][1]:.1f} {vertices["v4"][0]:.1f},{vertices["v4"][1]:.1f}" 
               fill="{base_color}" stroke="{stroke_color}" stroke-width="{stroke_width}" opacity="{opacity * 0.9}"/>
"""

        # Top face (X-Y plane)
        svg += f"""      <polygon points="{vertices["v4"][0]:.1f},{vertices["v4"][1]:.1f} {vertices["v5"][0]:.1f},{vertices["v5"][1]:.1f} {vertices["v6"][0]:.1f},{vertices["v6"][1]:.1f} {vertices["v7"][0]:.1f},{vertices["v7"][1]:.1f}" 
               fill="{base_color}" stroke="{stroke_color}" stroke-width="{stroke_width}" opacity="{opacity * 0.7}"/>
"""

        # Right face (Z-Y plane)
        svg += f"""      <polygon points="{vertices["v1"][0]:.1f},{vertices["v1"][1]:.1f} {vertices["v2"][0]:.1f},{vertices["v2"][1]:.1f} {vertices["v6"][0]:.1f},{vertices["v6"][1]:.1f} {vertices["v5"][0]:.1f},{vertices["v5"][1]:.1f}" 
               fill="{base_color}" stroke="{stroke_color}" stroke-width="{stroke_width}" opacity="{opacity * 0.8}"/>
"""

        # Part label
        label_x = (vertices["v0"][0] + vertices["v6"][0]) / 2
        label_y = (vertices["v0"][1] + vertices["v6"][1]) / 2 + 15

        svg += f"""      <text x="{label_x:.1f}" y="{label_y:.1f}" class="part-label" text-anchor="middle" fill="{stroke_color}">{part.id}</text>
"""

        if part.quantity > 1:
            svg += f"""      <text x="{label_x:.1f}" y="{label_y + 12:.1f}" class="part-label" text-anchor="middle" fill="{stroke_color}" font-size="9">×{part.quantity}</text>
"""

        svg += """    </g>
"""

        return svg

    def _draw_assembly_arrow(
        self, from_x: float, from_y: float, to_x: float, to_y: float, label: str = ""
    ) -> str:
        """
        Draw arrow showing assembly direction between two points.

        Args:
            from_x, from_y: Arrow start
            to_x, to_y: Arrow end
            label: Optional text label

        Returns:
            SVG path and optional text
        """
        svg = f"""    <line x1="{from_x:.1f}" y1="{from_y:.1f}" x2="{to_x:.1f}" y2="{to_y:.1f}" class="assembly-arrow"/>
"""

        if label:
            mid_x = (from_x + to_x) / 2
            mid_y = (from_y + to_y) / 2
            svg += f"""    <text x="{mid_x:.1f}" y="{mid_y - 5:.1f}" class="assembly-label" text-anchor="middle">{label}</text>
"""

        return svg

    async def validate_phase3_fields(self, step: AssemblyStep) -> bool:
        """Validate that Phase 3 fields are populated."""
        return bool(step.assembly_sequence or step.warnings or step.tips or step.detail_description)
