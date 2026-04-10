"""Stage 4: Assembly Instruction Generation Service."""

import logging
from typing import List

from app.services.step_loader import PipelineStage
from app.models.schemas import Part, SvgDrawing, AssemblyStep

logger = logging.getLogger(__name__)


class AssemblyGeneratorService(PipelineStage):
    """
    Stage 4: Generate assembly instructions using LLM.

    Input:  Parts[] (from Stage 2), SvgDrawing[] (from Stage 3)
    Output: AssemblyStep[] (step-by-step instructions)
    """

    def __init__(self) -> None:
        self.name = "AssemblyGeneratorService"
        self.logger = logging.getLogger(__name__)

    async def validate_input(self, data: tuple) -> bool:
        """Validate parts and drawings."""
        parts, drawings = data
        return (
            isinstance(parts, list)
            and len(parts) > 0
            and isinstance(drawings, list)
            and len(drawings) > 0
        )

    async def process(
        self, parts: List[Part], drawings: List[SvgDrawing], preview_only: bool = False
    ) -> List[AssemblyStep]:
        """
        Generate assembly steps.

        MOCK: Returns sample assembly steps for testing infrastructure.
        """

        is_valid = await self.validate_input((parts, drawings))
        if not is_valid:
            raise ValueError("Invalid parts or drawings input")

        self.logger.info(f"Generating assembly instructions (preview_only={preview_only})...")

        # MOCK: Generate sample assembly steps
        steps = [
            AssemblyStep(
                step_number=1,
                title="Prepare the components",
                description="Gather all components and lay them out on a flat surface.",
                part_indices=[0, 1],
                part_roles={0: "main panel", 1: "hardware"},
                context_part_indices=[],
                svg_diagram="<svg><!-- Exploded view --></svg>",
                duration_minutes=5,
            ),
            AssemblyStep(
                step_number=2,
                title="Connect side panels",
                description="Attach the side panels using the provided hardware.",
                part_indices=[1],
                part_roles={1: "connecting hardware"},
                context_part_indices=[0],
                svg_diagram="<svg><!-- Assembly step 2 --></svg>",
                duration_minutes=10,
            ),
        ]

        self.logger.info(f"Generated {len(steps)} assembly steps")
        return steps
