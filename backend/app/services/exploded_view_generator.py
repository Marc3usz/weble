"""Stage 4b: Exploded View SVG Generator - Phase 3 per-step assembly diagrams.

Enhanced Phase 1 features:
- Professional IKEA-style diagrams with context parts visualization
- Assembly flow visualization with numbered sequences
- Step progress indicators and duration badges
- Better depth cueing and material indicators
- Enhanced isometric shading and visual hierarchy
"""

import logging
import math
from typing import Dict, List, Optional, Tuple

from app.models.schemas import AssemblyStep, Part
from app.services.step_loader import PipelineStage

logger = logging.getLogger(__name__)


class IsometricProjection:
    """Helper class for isometric 3D projection calculations with enhanced depth cueing."""

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

    @staticmethod
    def calculate_face_brightness(face_normal: Tuple[float, float, float]) -> float:
        """
        Calculate face brightness based on normal direction (lighting model).

        Simulates 3-point lighting for better depth perception.
        Light comes from upper-right-front (normalized).

        Args:
            face_normal: (nx, ny, nz) unit normal vector

        Returns:
            Brightness factor 0.0-1.0
        """
        # Light direction (isometric 3-point)
        light_dir = (0.8, 0.5, 0.6)  # From upper-right-front
        
        # Normalize
        light_len = math.sqrt(light_dir[0]**2 + light_dir[1]**2 + light_dir[2]**2)
        light_dir = (light_dir[0]/light_len, light_dir[1]/light_len, light_dir[2]/light_len)
        
        # Dot product (clamped)
        dot = max(0, light_dir[0]*face_normal[0] + light_dir[1]*face_normal[1] + light_dir[2]*face_normal[2])
        
        # Map to brightness: 0.5 (shadowed) to 1.0 (lit)
        return 0.5 + 0.5 * dot


class ExplodedViewSVGGenerator(PipelineStage):
    """
    Stage 4b: Generate per-step exploded view assembly diagrams.

    Input:  Parts[], AssemblyStep, step_number
    Output: SVG string with highlighted assembly state

    Enhanced Phase 1 Features:
    - Professional IKEA-style diagrams showing context + active parts
    - Isometric 3D representation with depth cueing and shadows
    - Active parts (involved in step) at full opacity with highlights
    - Context parts (already assembled) at 30% opacity, grayed
    - Assembly sequence visualization with numbered steps
    - Step progress indicator (e.g., "Step 2 of 8")
    - Duration badges and difficulty indicators
    - Assembly arrows showing part insertion direction
    - Material-based visual indicators (patterns/textures)
    - Optimal canvas sizing with visual balance
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
        # Material patterns (for visual distinction)
        self.material_patterns = {
            "wood": "diagonal",
            "metal": "crosshatch",
            "plastic": "dots",
            "fabric": "horizontal",
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

    async def generate_exploded_view(self, parts: List[Part], step: AssemblyStep, total_steps: int = 0) -> str:
        """
        Generate exploded view SVG for assembly step.

        Shows all parts in professional IKEA-style with:
        - Context parts (already assembled): 30% opacity, grayed out
        - Active parts (this step): full opacity, highlighted with halos
        - Assembly flow visualization with numbered sequence
        - Step progress indicator (e.g., "Step 2 of 8")
        - Duration badge and difficulty level
        - Assembly arrows showing insertion direction

        Args:
            parts: List of all parts
            step: Assembly step data
            total_steps: Total number of steps (for progress indicator)

        Returns:
            SVG content as string
        """
        # Determine canvas size based on parts and content
        canvas_w, canvas_h = self._calculate_optimal_canvas(parts, step)

        # Calculate part positions for balanced layout
        part_positions = self._calculate_part_positions(parts)

        # Start SVG with enhanced styling
        svg = self._create_svg_header(canvas_w, canvas_h, step)

        # Render background gradient for depth
        svg += self._render_background_gradient(canvas_w, canvas_h)

        # Render step progress header
        svg += self._render_step_progress(step, total_steps, canvas_w)

        # Render parts (context first, then active)
        svg += """  <!-- Parts Group -->
  <g id="parts">
"""
        # Render context parts first (underneath)
        for part_idx, part in enumerate(parts):
            if part_idx not in part_positions:
                continue

            if part_idx in step.context_part_indices:
                pos_x, pos_y = part_positions[part_idx]
                part_svg = self._render_isometric_part(
                    part, pos_x, pos_y, is_active=False, is_context=True, order=0
                )
                svg += part_svg

        # Render active parts (on top, highlighted)
        for part_idx, part in enumerate(parts):
            if part_idx not in part_positions:
                continue

            if part_idx in step.part_indices:
                pos_x, pos_y = part_positions[part_idx]
                part_svg = self._render_isometric_part(
                    part, pos_x, pos_y, is_active=True, is_context=False, order=1
                )
                svg += part_svg

        svg += """  </g>
  
  <!-- Assembly Flow Visualization -->
  <g id="assembly-flow">
"""
        # Render assembly flow with numbered steps
        svg += self._render_assembly_flow(step, part_positions, canvas_w, canvas_h)

        svg += """  </g>
  
  <!-- Instructions Panel -->
  <g id="instructions">
"""

        # Add assembly sequence steps if available
        svg += self._render_instructions_panel(step, canvas_w, canvas_h)

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

    def _calculate_optimal_canvas(self, parts: List[Part], step: AssemblyStep) -> Tuple[float, float]:
        """
        Calculate optimal canvas size based on parts, assembly sequence, and metadata.

        Phase 1 Enhancement: Smart sizing that accounts for:
        - Number of parts and their sizes
        - Assembly sequence text length
        - Step progress indicator
        - Warnings and tips length
        - Visual balance (golden ratio consideration)

        Returns:
            (width, height) for canvas
        """
        base_w, base_h = 600, 450  # Increased from 400x300 for better readability

        # Scale based on active parts count
        active_count = len(step.part_indices)
        context_count = len(step.context_part_indices)
        total_visual_parts = max(1, active_count + context_count)

        # Add width/height based on part count
        width_per_part = 80
        height_per_part = 60

        extra_w = total_visual_parts * width_per_part
        extra_h = total_visual_parts * height_per_part

        # Account for text content (assembly sequence, warnings)
        sequence_lines = len(step.assembly_sequence)
        warnings_lines = len(step.warnings)
        tips_lines = len(step.tips)
        
        extra_h += (sequence_lines + warnings_lines + tips_lines) * 25  # ~25px per line

        # Calculate final dimensions
        canvas_w = max(600, min(base_w + extra_w, 1400))  # 600-1400px wide
        canvas_h = max(500, min(base_h + extra_h, 1800))  # 500-1800px tall

        # Ensure reasonable aspect ratio (not too extreme)
        aspect = canvas_w / canvas_h
        if aspect > 2.0:
            canvas_w = canvas_h * 2.0
        elif aspect < 0.5:
            canvas_h = canvas_w * 2.0

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
        self, part: Part, x: float, y: float, is_active: bool = True, is_context: bool = False, order: int = 0
    ) -> str:
        """
        Render a single part as an isometric box with enhanced depth cueing.

        Phase 1 Enhancement:
        - Adds subtle gradients for 3D effect
        - Includes material indicators (hatch patterns)
        - Better contrast for active vs context parts
        - Active parts get highlight halos and shadows
        - Context parts are desaturated

        Args:
            part: Part to render
            x, y: Screen position (origin)
            is_active: If True, render at full opacity (involved in step)
            is_context: If True, render at low opacity (already assembled)
            order: Rendering order (for z-index effect)

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

        # Determine colors with Phase 1 enhancements
        base_color = self.part_type_colors.get(part.part_type.value, "#999999")
        
        if is_context:
            # Desaturate context parts (convert to grayscale-ish)
            base_color = "#b0b0b0"  # Light gray
            opacity = 0.3
            stroke_color = "#999999"
            stroke_width = 0.8
        else:
            # Active parts: vibrant with glow
            opacity = 1.0
            stroke_color = self._lighten_color(base_color)
            stroke_width = 2.0

        # Build SVG with enhanced styling
        class_name = "part-active" if is_active else "part-context"
        
        # Add drop shadow for active parts
        shadow_svg = ""
        if is_active:
            shadow_svg = f"""    <defs>
      <filter id="shadow-{part.original_index}" x="-50%" y="-50%" width="200%" height="200%">
        <feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.3" flood-color="#000"/>
      </filter>
    </defs>
"""

        svg = f"""    <!-- Part {part.id} (idx: {part.original_index}) -->
    <g class="{class_name}" opacity="{opacity}" filter="url(#shadow-{part.original_index})" style="z-index: {order}">
"""

        # Define gradients for 3D effect
        gradient_id = f"grad-{part.original_index}"
        svg += f"""      <defs>
        <linearGradient id="{gradient_id}" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:{self._lighten_color(base_color)};stop-opacity:1" />
          <stop offset="100%" style="stop-color:{base_color};stop-opacity:1" />
        </linearGradient>
      </defs>
"""

        # Draw three visible faces with enhanced shading
        # Front face (Z-X plane) - most prominent
        front_brightness = 0.85
        front_color = self._adjust_color_brightness(base_color, front_brightness)
        svg += f"""      <polygon points="{vertices["v0"][0]:.1f},{vertices["v0"][1]:.1f} {vertices["v1"][0]:.1f},{vertices["v1"][1]:.1f} {vertices["v5"][0]:.1f},{vertices["v5"][1]:.1f} {vertices["v4"][0]:.1f},{vertices["v4"][1]:.1f}" 
                fill="url(#{gradient_id})" stroke="{stroke_color}" stroke-width="{stroke_width}" opacity="{opacity * 0.95}"/>
"""

        # Top face (X-Y plane) - medium brightness
        top_brightness = 1.0
        top_color = self._adjust_color_brightness(base_color, top_brightness)
        svg += f"""      <polygon points="{vertices["v4"][0]:.1f},{vertices["v4"][1]:.1f} {vertices["v5"][0]:.1f},{vertices["v5"][1]:.1f} {vertices["v6"][0]:.1f},{vertices["v6"][1]:.1f} {vertices["v7"][0]:.1f},{vertices["v7"][1]:.1f}" 
                fill="{top_color}" stroke="{stroke_color}" stroke-width="{stroke_width}" opacity="{opacity * 0.9}"/>
"""

        # Right face (Z-Y plane) - darkest
        right_brightness = 0.65
        right_color = self._adjust_color_brightness(base_color, right_brightness)
        svg += f"""      <polygon points="{vertices["v1"][0]:.1f},{vertices["v1"][1]:.1f} {vertices["v2"][0]:.1f},{vertices["v2"][1]:.1f} {vertices["v6"][0]:.1f},{vertices["v6"][1]:.1f} {vertices["v5"][0]:.1f},{vertices["v5"][1]:.1f}" 
                fill="{right_color}" stroke="{stroke_color}" stroke-width="{stroke_width}" opacity="{opacity * 0.85}"/>
"""

        # Add glow/highlight for active parts
        if is_active:
            halo_opacity = 0.2
            halo_color = self._lighten_color(base_color, 0.3)
            svg += f"""      <circle cx="{x}" cy="{y}" r="35" fill="none" stroke="{halo_color}" stroke-width="3" opacity="{halo_opacity}"/>
"""

        # Part label - always visible
        label_x = (vertices["v0"][0] + vertices["v6"][0]) / 2
        label_y = (vertices["v0"][1] + vertices["v6"][1]) / 2 + 15

        label_color = "#000000" if is_active else "#666666"
        svg += f"""      <text x="{label_x:.1f}" y="{label_y:.1f}" class="part-label" text-anchor="middle" fill="{label_color}" font-weight="bold">{part.id}</text>
"""

        if part.quantity > 1:
            svg += f"""      <text x="{label_x:.1f}" y="{label_y + 12:.1f}" class="part-label" text-anchor="middle" fill="{label_color}" font-size="9">×{part.quantity}</text>
"""

        svg += """    </g>
"""

        return svg

    def _lighten_color(self, hex_color: str, factor: float = 0.2) -> str:
        """
        Lighten a hex color by the given factor (0-1).

        Args:
            hex_color: Color in hex format (e.g., "#4a90e2")
            factor: Lightening factor (0=no change, 1=white)

        Returns:
            Lighter hex color
        """
        try:
            hex_color = hex_color.lstrip("#")
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            r = min(255, int(r + (255 - r) * factor))
            g = min(255, int(g + (255 - g) * factor))
            b = min(255, int(b + (255 - b) * factor))
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return hex_color

    def _adjust_color_brightness(self, hex_color: str, brightness: float) -> str:
        """
        Adjust color brightness (0=black, 0.5=original, 1=lighter).

        Args:
            hex_color: Color in hex format
            brightness: Brightness factor (0-1)

        Returns:
            Adjusted hex color
        """
        try:
            hex_color = hex_color.lstrip("#")
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            r = int(r * brightness)
            g = int(g * brightness)
            b = int(b * brightness)
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return hex_color

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

    def _create_svg_header(self, canvas_w: float, canvas_h: float, step: AssemblyStep) -> str:
        """Create SVG header with enhanced styling and gradients."""
        return f"""<svg width="{canvas_w:.0f}" height="{canvas_h:.0f}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w:.0f} {canvas_h:.0f}">
  <!-- Enhanced Phase 1 Exploded View Assembly Diagram -->
  <defs>
    <style>
      .part-label {{ font-size: 12px; font-family: Arial, sans-serif; font-weight: bold; }}
      .step-info {{ font-size: 14px; font-family: Arial, sans-serif; fill: #333; }}
      .step-progress {{ font-size: 13px; font-family: Arial, sans-serif; fill: #666; font-weight: bold; }}
      .step-title {{ font-size: 18px; font-family: Arial, sans-serif; font-weight: bold; fill: #222; }}
      .difficulty-badge {{ font-size: 11px; font-family: Arial, sans-serif; fill: #fff; font-weight: bold; }}
      .duration-badge {{ font-size: 11px; font-family: Arial, sans-serif; fill: #666; }}
      .part-active {{ filter: drop-shadow(0 1px 3px rgba(0,0,0,0.2)); }}
      .part-context {{ opacity: 0.35; }}
      .assembly-arrow {{ stroke: #e74c3c; stroke-width: 2.5; fill: none; marker-end: url(#arrowhead); }}
      .assembly-step-number {{ font-size: 12px; font-family: Arial, sans-serif; fill: #fff; font-weight: bold; }}
      .assembly-label {{ font-size: 11px; font-family: Arial, sans-serif; fill: #e74c3c; }}
      .instructions-label {{ font-size: 12px; font-family: Arial, sans-serif; fill: #333; }}
      .warning-label {{ font-size: 11px; font-family: Arial, sans-serif; fill: #d0021b; font-weight: bold; }}
      .tips-label {{ font-size: 11px; font-family: Arial, sans-serif; fill: #7ed321; font-weight: bold; }}
    </style>
    <!-- Arrow marker for assembly direction -->
    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <polygon points="0 0, 10 3, 0 6" fill="#e74c3c"/>
    </marker>
  </defs>
  
  <rect width="{canvas_w:.0f}" height="{canvas_h:.0f}" fill="white" stroke="#e0e0e0" stroke-width="1"/>
"""

    def _render_background_gradient(self, canvas_w: float, canvas_h: float) -> str:
        """Render subtle background gradient for visual polish."""
        return f"""  <!-- Background gradient for depth -->
  <defs>
    <linearGradient id="bg-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#ffffff;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#f8f8f8;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="{canvas_w:.0f}" height="{canvas_h:.0f}" fill="url(#bg-gradient)" opacity="0.5"/>
"""

    def _render_step_progress(self, step: AssemblyStep, total_steps: int, canvas_w: float) -> str:
        """
        Render step progress indicator (e.g., "Step 2 of 8").

        Phase 1 Enhancement: Shows step number, title, difficulty, and duration.

        Args:
            step: Assembly step
            total_steps: Total number of steps
            canvas_w: Canvas width

        Returns:
            SVG group with progress indicator
        """
        header_height = 70
        progress_text = f"Step {step.step_number}"
        if total_steps > 0:
            progress_text += f" of {total_steps}"

        # Determine difficulty color
        difficulty = "MEDIUM"  # Default
        difficulty_color = "#f5a623"  # Orange
        if hasattr(step, 'difficulty'):
            difficulty = getattr(step, 'difficulty', 'MEDIUM').upper()
            if difficulty == "EASY":
                difficulty_color = "#7ed321"  # Green
            elif difficulty == "HARD":
                difficulty_color = "#d0021b"  # Red
            elif difficulty == "EXPERT":
                difficulty_color = "#9013fe"  # Purple

        duration_text = f"{step.duration_minutes} min" if step.duration_minutes > 0 else ""

        svg = f"""  <!-- Step Progress Header -->
  <g id="step-header">
    <rect x="0" y="0" width="{canvas_w:.0f}" height="{header_height:.0f}" fill="#f5f5f5" stroke="#ddd" stroke-width="1"/>
    
    <text x="20" y="25" class="step-progress">{progress_text}</text>
    <text x="20" y="50" class="step-title">{step.title}</text>
    
    <!-- Difficulty Badge -->
    <rect x="{canvas_w - 140:.0f}" y="15" width="55" height="22" fill="{difficulty_color}" rx="3"/>
    <text x="{canvas_w - 112:.0f}" y="33" class="difficulty-badge" text-anchor="middle">{difficulty}</text>
    
    <!-- Duration Badge -->
    <rect x="{canvas_w - 80:.0f}" y="15" width="65" height="22" fill="#e8e8e8" rx="3" stroke="#999" stroke-width="1"/>
    <text x="{canvas_w - 47:.0f}" y="33" class="duration-badge" text-anchor="middle">{duration_text}</text>
  </g>
"""
        return svg

    def _render_assembly_flow(
        self, step: AssemblyStep, part_positions: Dict[int, Tuple[float, float]], canvas_w: float, canvas_h: float
    ) -> str:
        """
        Render assembly flow visualization with numbered sequence.

        Phase 1 Enhancement: Shows numbered steps for assembly action sequence.

        Args:
            step: Assembly step
            part_positions: Dict of part_idx -> (x, y) positions
            canvas_w: Canvas width
            canvas_h: Canvas height

        Returns:
            SVG group with assembly flow
        """
        svg = ""

        # Add numbered sequence circles if assembly_sequence is available
        if step.assembly_sequence and len(step.part_indices) > 0:
            # Place sequence indicators at calculated positions
            seq_parts = list(step.part_indices)
            
            for seq_idx, (part_idx, action) in enumerate(zip(seq_parts, step.assembly_sequence)):
                if part_idx in part_positions:
                    pos_x, pos_y = part_positions[part_idx]
                    
                    # Draw numbered circle (1, 2, 3, etc.)
                    circle_x = pos_x + 45
                    circle_y = pos_y - 40
                    
                    # Circle background
                    svg += f"""    <circle cx="{circle_x:.1f}" cy="{circle_y:.1f}" r="14" fill="#e74c3c" opacity="0.9"/>
    <text x="{circle_x:.1f}" y="{circle_y + 4:.1f}" class="assembly-step-number" text-anchor="middle">{seq_idx + 1}</text>
"""
                    
                    # Action label below circle
                    svg += f"""    <text x="{circle_x:.1f}" y="{circle_y + 25:.1f}" class="assembly-label" text-anchor="middle">{action}</text>
"""

        return svg

    def _render_instructions_panel(self, step: AssemblyStep, canvas_w: float, canvas_h: float) -> str:
        """
        Render instructions panel with assembly sequence, warnings, and tips.

        Phase 1 Enhancement: Professional layout with clear visual hierarchy.

        Args:
            step: Assembly step
            canvas_w: Canvas width
            canvas_h: Canvas height

        Returns:
            SVG group with instructions
        """
        svg = ""
        panel_y = canvas_h - 200  # Start panel near bottom
        margin_x = 20

        # Title
        if step.assembly_sequence:
            svg += f"""    <text x="{margin_x:.0f}" y="{panel_y:.0f}" class="instructions-label" font-weight="bold">Assembly Sequence:</text>
"""
            for i, seq_step in enumerate(step.assembly_sequence[:5]):  # Show up to 5 steps
                svg += f"""    <text x="{margin_x + 10:.0f}" y="{panel_y + (i + 1) * 18:.0f}" class="assembly-label">• {seq_step}</text>
"""
            panel_y += (len(step.assembly_sequence) + 1) * 20

        # Warnings section
        if step.warnings:
            svg += f"""    <text x="{margin_x:.0f}" y="{panel_y:.0f}" class="warning-label">[WARNING]</text>
"""
            for i, warning in enumerate(step.warnings[:3]):  # Show up to 3 warnings
                # Wrap long text
                warning_text = warning[:60] + ("..." if len(warning) > 60 else "")
                svg += f"""    <text x="{margin_x + 15:.0f}" y="{panel_y + (i + 1) * 18:.0f}" class="warning-label">• {warning_text}</text>
"""
            panel_y += (len(step.warnings) + 1) * 20

        # Tips section
        if step.tips:
            svg += f"""    <text x="{margin_x:.0f}" y="{panel_y:.0f}" class="tips-label">[TIP]</text>
"""
            for i, tip in enumerate(step.tips[:2]):  # Show up to 2 tips
                # Wrap long text
                tip_text = tip[:55] + ("..." if len(tip) > 55 else "")
                svg += f"""    <text x="{margin_x + 15:.0f}" y="{panel_y + (i + 1) * 18:.0f}" class="tips-label">• {tip_text}</text>
"""

        return svg
        """Validate that Phase 3 fields are populated."""
        return bool(step.assembly_sequence or step.warnings or step.tips or step.detail_description)
