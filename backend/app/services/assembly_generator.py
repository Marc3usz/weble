"""Stage 4: Assembly Instruction Generation Service."""

import logging
from collections import defaultdict
from typing import List

from app.services.step_loader import PipelineStage
from app.models.schemas import AssemblyStep, Part, PartType, SvgDrawing

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
        if not isinstance(data, tuple) or len(data) != 2:
            return False
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

        Current implementation uses deterministic rule-based sequencing as an
        MVP fallback to keep the pipeline robust before full LLM integration.
        """

        is_valid = await self.validate_input((parts, drawings))
        if not is_valid:
            raise ValueError("Invalid parts or drawings input")

        self.logger.info(f"Generating assembly instructions (preview_only={preview_only})...")

        classified_indices = defaultdict(list)
        for idx, part in enumerate(parts):
            classified_indices[part.part_type].append(idx)

        panel_indices = classified_indices.get(PartType.PANEL, [])
        structural_indices = classified_indices.get(PartType.STRUCTURAL, [])
        hardware_indices = classified_indices.get(PartType.HARDWARE, [])
        fastener_indices = classified_indices.get(PartType.FASTENER, [])
        other_indices = classified_indices.get(PartType.OTHER, [])

        frame_indices = panel_indices + structural_indices
        connector_indices = hardware_indices + fastener_indices

        steps: List[AssemblyStep] = []
        current_step = 1

        if preview_only:
            active = frame_indices[: min(3, len(frame_indices))] or [0]
            steps.append(
                AssemblyStep(
                    step_number=1,
                    title="Preview assembly layout",
                    description=(
                        "This is a quick overview of the primary structural parts "
                        "and their expected placement."
                    ),
                    part_indices=active,
                    part_roles={idx: "primary component" for idx in active},
                    context_part_indices=[],
                    svg_diagram=self._simple_step_svg("Preview", active),
                    duration_minutes=2,
                )
            )
            context = active
            connectors = connector_indices[:1] or ([1] if len(parts) > 1 else active)
            steps.append(
                AssemblyStep(
                    step_number=2,
                    title="Preview connectors and fit",
                    description=(
                        "Review where connectors or hardware align with the base "
                        "structure before full assembly."
                    ),
                    part_indices=connectors,
                    part_roles={idx: "connector" for idx in connectors},
                    context_part_indices=context,
                    svg_diagram=self._simple_step_svg("Preview Fit", connectors),
                    duration_minutes=2,
                )
            )
            return steps

        if frame_indices:
            active = frame_indices[: min(3, len(frame_indices))]
            steps.append(
                AssemblyStep(
                    step_number=current_step,
                    title="Assemble main frame",
                    description=(
                        "Align the main frame components on a flat surface and "
                        "join them to establish the base structure."
                    ),
                    part_indices=active,
                    part_roles={idx: "frame component" for idx in active},
                    context_part_indices=[],
                    svg_diagram=self._simple_step_svg("Frame", active),
                    duration_minutes=8,
                )
            )
            current_step += 1

        if connector_indices:
            context = frame_indices[: min(3, len(frame_indices))]
            active = connector_indices[: min(5, len(connector_indices))]
            steps.append(
                AssemblyStep(
                    step_number=current_step,
                    title="Install hardware and fasteners",
                    description=(
                        "Attach hardware elements and insert fasteners to secure "
                        "the assembled frame sections."
                    ),
                    part_indices=active,
                    part_roles={idx: "connector" for idx in active},
                    context_part_indices=context,
                    svg_diagram=self._simple_step_svg("Hardware", active),
                    duration_minutes=10,
                )
            )
            current_step += 1

        if other_indices:
            context = (
                frame_indices[: min(3, len(frame_indices))]
                + connector_indices[: min(3, len(connector_indices))]
            )
            active = other_indices[: min(4, len(other_indices))]
            steps.append(
                AssemblyStep(
                    step_number=current_step,
                    title="Attach remaining components",
                    description=(
                        "Mount the remaining components and verify all joints are "
                        "aligned before final tightening."
                    ),
                    part_indices=active,
                    part_roles={idx: "secondary component" for idx in active},
                    context_part_indices=context,
                    svg_diagram=self._simple_step_svg("Finalize", active),
                    duration_minutes=7,
                )
            )

        if not steps:
            steps = [
                AssemblyStep(
                    step_number=1,
                    title="Prepare components",
                    description="Organize the detected parts and verify quantities before assembly.",
                    part_indices=[0],
                    part_roles={0: "component"},
                    context_part_indices=[],
                    svg_diagram=self._simple_step_svg("Prepare", [0]),
                    duration_minutes=3,
                )
            ]

        self.logger.info(f"Generated {len(steps)} assembly steps")
        return steps

    @staticmethod
    def _simple_step_svg(title: str, indices: List[int]) -> str:
        labels = ", ".join(str(i) for i in indices)
        return (
            "<svg width='260' height='120' xmlns='http://www.w3.org/2000/svg'>"
            "<rect x='1' y='1' width='258' height='118' fill='white' stroke='#333'/>"
            f"<text x='14' y='28' font-size='14' font-family='Arial, sans-serif'>{title}</text>"
            f"<text x='14' y='54' font-size='12' font-family='Arial, sans-serif'>Parts: {labels}</text>"
            "</svg>"
        )
