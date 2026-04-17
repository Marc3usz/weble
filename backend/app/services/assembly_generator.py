"""Stage 4: Assembly Instruction Generation Service with Phase 3 LLM Support."""

import logging
from collections import defaultdict
from typing import List, Optional

from app.core.config import AssemblyTone, settings
from app.models.schemas import AssemblyStep, Part, PartType, SvgDrawing
from app.services.step_loader import PipelineStage

logger = logging.getLogger(__name__)


class AssemblyGeneratorService(PipelineStage):
    """
    Stage 4: Generate assembly instructions using LLM (Phase 3) with rule-based fallback.

    Input:  Parts[] (from Stage 2), SvgDrawing[] (from Stage 3)
    Output: AssemblyStep[] (step-by-step instructions)

    Phase 3 Enhancement:
    - Optional LLM service for AI-generated instructions
    - Tone-aware generation (IKEA, TECHNICAL, BEGINNER)
    - Fallback to rules if LLM unavailable
    - Per-step exploded view diagrams
    """

    def __init__(self, llm_service: Optional["LLMAssemblyGeneratorService"] = None) -> None:  # noqa: F821
        self.name = "AssemblyGeneratorService"
        self.logger = logging.getLogger(__name__)
        self.llm_service = llm_service

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
        self,
        parts: List[Part],
        drawings: List[SvgDrawing],
        tone: AssemblyTone = AssemblyTone.IKEA,
        preview_only: bool = False,
    ) -> List[AssemblyStep]:
        """
        Generate assembly steps using LLM (Phase 3) or rules-based fallback.

        Args:
            parts: List of parts to assemble
            drawings: List of SVG drawings
            tone: Assembly instruction tone (IKEA, TECHNICAL, BEGINNER)
            preview_only: If True, return only preview steps

        Returns:
            List of AssemblyStep objects
        """
        is_valid = await self.validate_input((parts, drawings))
        if not is_valid:
            raise ValueError("Invalid parts or drawings input")

        self.logger.info(
            f"Generating assembly instructions (preview_only={preview_only}, "
            f"llm_enabled={settings.assembly_llm_enabled})..."
        )

        # Preview mode (simplified output for quick visualization)
        if preview_only:
            return await self._generate_preview_steps(parts, drawings)

        # Try LLM if enabled and available
        if settings.assembly_llm_enabled and self.llm_service:
            try:
                self.logger.debug("Attempting LLM-based assembly generation...")
                steps = await self.llm_service.process(parts, drawings, tone)
                # Add exploded views to each step
                from app.services.exploded_view_generator import ExplodedViewSVGGenerator

                svg_gen = ExplodedViewSVGGenerator()
                for step in steps:
                    step.exploded_view_svg = await svg_gen.generate_exploded_view(parts, step)
                self.logger.info(f"Generated {len(steps)} steps using LLM")
                return steps
            except Exception as e:
                self.logger.warning(
                    f"LLM assembly generation failed ({e}), falling back to rules..."
                )
                # Fall through to rules-based generation

        # Rule-based fallback
        steps = await self._generate_rules_based_steps(parts, drawings, tone)

        # Add exploded views
        try:
            from app.services.exploded_view_generator import ExplodedViewSVGGenerator

            svg_gen = ExplodedViewSVGGenerator()
            for step in steps:
                step.exploded_view_svg = await svg_gen.generate_exploded_view(parts, step)
        except Exception as e:
            self.logger.warning(f"Could not generate exploded views: {e}")

        self.logger.info(f"Generated {len(steps)} assembly steps (rule-based)")
        return steps

    # =========================================================================
    # PREVIEW GENERATION
    # =========================================================================

    async def _generate_preview_steps(
        self, parts: List[Part], drawings: List[SvgDrawing]
    ) -> List[AssemblyStep]:
        """Generate quick preview steps for visualization."""
        classified_indices = defaultdict(list)
        for idx, part in enumerate(parts):
            classified_indices[part.part_type].append(idx)

        panel_indices = classified_indices.get(PartType.PANEL, [])
        structural_indices = classified_indices.get(PartType.STRUCTURAL, [])
        hardware_indices = classified_indices.get(PartType.HARDWARE, [])
        fastener_indices = classified_indices.get(PartType.FASTENER, [])

        frame_indices = panel_indices + structural_indices
        connector_indices = hardware_indices + fastener_indices

        steps: List[AssemblyStep] = []

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
                is_llm_generated=False,
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
                is_llm_generated=False,
            )
        )

        return steps

    # =========================================================================
    # RULE-BASED GENERATION (Fallback)
    # =========================================================================

    async def _generate_rules_based_steps(
        self, parts: List[Part], drawings: List[SvgDrawing], tone: AssemblyTone
    ) -> List[AssemblyStep]:
        """Generate assembly steps using rule-based logic."""
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

        # Single part special case
        if len(parts) == 1:
            return [
                AssemblyStep(
                    step_number=1,
                    title="Assembly complete",
                    description="No assembly required - part is ready to use",
                    part_indices=[0],
                    part_roles={0: "complete assembly"},
                    context_part_indices=[],
                    svg_diagram=self._simple_step_svg("Ready", [0]),
                    duration_minutes=0,
                    confidence_score=0.9,
                    is_llm_generated=False,
                )
            ]

        # Step 1: Frame assembly
        if frame_indices:
            active = frame_indices[: min(3, len(frame_indices))]
            title, desc, detail = self._get_step_text(tone, "frame")
            steps.append(
                AssemblyStep(
                    step_number=current_step,
                    title=title,
                    description=desc,
                    detail_description=detail,
                    part_indices=active,
                    part_roles={idx: "frame component" for idx in active},
                    context_part_indices=[],
                    assembly_sequence=["Align", "Secure"],
                    warnings=self._get_step_warnings(tone, "frame"),
                    tips=self._get_step_tips(tone, "frame"),
                    svg_diagram=self._simple_step_svg("Frame", active),
                    duration_minutes=8,
                    confidence_score=0.7,
                    is_llm_generated=False,
                )
            )
            current_step += 1

        # Step 2: Hardware and fasteners
        if connector_indices:
            context = frame_indices[: min(3, len(frame_indices))]
            active = connector_indices[: min(5, len(connector_indices))]
            title, desc, detail = self._get_step_text(tone, "hardware")
            steps.append(
                AssemblyStep(
                    step_number=current_step,
                    title=title,
                    description=desc,
                    detail_description=detail,
                    part_indices=active,
                    part_roles={idx: "connector" for idx in active},
                    context_part_indices=context,
                    assembly_sequence=["Position", "Tighten"],
                    warnings=self._get_step_warnings(tone, "hardware"),
                    tips=self._get_step_tips(tone, "hardware"),
                    svg_diagram=self._simple_step_svg("Hardware", active),
                    duration_minutes=10,
                    confidence_score=0.7,
                    is_llm_generated=False,
                )
            )
            current_step += 1

        # Step 3: Remaining components
        if other_indices:
            context = (
                frame_indices[: min(3, len(frame_indices))]
                + connector_indices[: min(3, len(connector_indices))]
            )
            active = other_indices[: min(4, len(other_indices))]
            title, desc, detail = self._get_step_text(tone, "remaining")
            steps.append(
                AssemblyStep(
                    step_number=current_step,
                    title=title,
                    description=desc,
                    detail_description=detail,
                    part_indices=active,
                    part_roles={idx: "secondary component" for idx in active},
                    context_part_indices=context,
                    assembly_sequence=["Mount", "Verify"],
                    warnings=self._get_step_warnings(tone, "remaining"),
                    tips=self._get_step_tips(tone, "remaining"),
                    svg_diagram=self._simple_step_svg("Finalize", active),
                    duration_minutes=7,
                    confidence_score=0.7,
                    is_llm_generated=False,
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
                    is_llm_generated=False,
                )
            ]

        return steps

    # =========================================================================
    # TONE-SPECIFIC TEXT GENERATION
    # =========================================================================

    def _get_step_text(self, tone: AssemblyTone, step_type: str) -> tuple:
        """Get tone-appropriate title, description, and detail for a step type."""
        text_map = {
            "frame": {
                AssemblyTone.IKEA: (
                    "Build the main frame (fun part!)",
                    "Assemble the primary frame components",
                    "Let's build the main structure! Align the frame pieces and secure them together. You're doing great!",
                ),
                AssemblyTone.TECHNICAL: (
                    "Assemble structural frame",
                    "Connect primary structural components with proper alignment",
                    "Position frame components with ±2mm tolerance. Ensure orthogonal alignment before fastening.",
                ),
                AssemblyTone.BEGINNER: (
                    "Build the main frame (take your time!)",
                    "Assemble the frame pieces carefully",
                    "Don't worry, this is the easier part! Just align the pieces and push them together gently. They should click or fit snugly.",
                ),
            },
            "hardware": {
                AssemblyTone.IKEA: (
                    "Snap on the hardware",
                    "Install hardware components to secure the frame",
                    "Now for the fun part - let's make sure everything stays together!",
                ),
                AssemblyTone.TECHNICAL: (
                    "Install fastening hardware",
                    "Apply fastening elements per specification",
                    "Install fasteners to specification. Ensure proper torque and alignment.",
                ),
                AssemblyTone.BEGINNER: (
                    "Add the hardware pieces (be gentle!)",
                    "Install the hardware that holds things together",
                    "These pieces help hold everything secure. Be gentle and make sure each one sits properly.",
                ),
            },
            "remaining": {
                AssemblyTone.IKEA: (
                    "Add the finishing touches",
                    "Attach the remaining components",
                    "Almost done! Let's add these final pieces to complete your assembly.",
                ),
                AssemblyTone.TECHNICAL: (
                    "Install remaining components",
                    "Mount secondary components and verify alignment",
                    "Install remaining parts and verify all connections are secure.",
                ),
                AssemblyTone.BEGINNER: (
                    "Attach the last pieces",
                    "Add the remaining parts",
                    "Just a few more pieces to go! You're almost done!",
                ),
            },
        }
        return text_map.get(step_type, {}).get(tone, ("Step", "Continue assembly", "Keep going"))

    def _get_step_warnings(self, tone: AssemblyTone, step_type: str) -> List[str]:
        """Get tone-appropriate warnings for a step."""
        warnings_map = {
            "frame": {
                AssemblyTone.IKEA: ["Make sure everything clicks securely"],
                AssemblyTone.TECHNICAL: ["Verify alignment and secure all joints"],
                AssemblyTone.BEGINNER: [
                    "Be very careful to align pieces before pushing them together"
                ],
            },
            "hardware": {
                AssemblyTone.IKEA: ["Don't over-tighten - snug is enough"],
                AssemblyTone.TECHNICAL: ["Do not exceed specified torque limits"],
                AssemblyTone.BEGINNER: [
                    "WARNING: Don't make them too tight or you might break something"
                ],
            },
            "remaining": {
                AssemblyTone.IKEA: ["Final check - everything should be solid"],
                AssemblyTone.TECHNICAL: ["Verify all components are properly seated"],
                AssemblyTone.BEGINNER: [
                    "Give everything a gentle tug to check - nothing should wiggle"
                ],
            },
        }
        return warnings_map.get(step_type, {}).get(tone, [])

    def _get_step_tips(self, tone: AssemblyTone, step_type: str) -> List[str]:
        """Get tone-appropriate tips for a step."""
        tips_map = {
            "frame": {
                AssemblyTone.IKEA: ["Use a flat surface to check alignment"],
                AssemblyTone.TECHNICAL: ["Use measuring instruments to verify alignment"],
                AssemblyTone.BEGINNER: ["It really helps to lay everything on a flat table"],
            },
            "hardware": {
                AssemblyTone.IKEA: ["Make sure each piece feels solid"],
                AssemblyTone.TECHNICAL: ["Apply fasteners in a cross pattern if multiple"],
                AssemblyTone.BEGINNER: ["When something feels snug, stop - don't keep turning"],
            },
            "remaining": {
                AssemblyTone.IKEA: ["You're almost there!"],
                AssemblyTone.TECHNICAL: ["Document final assembly state for reference"],
                AssemblyTone.BEGINNER: ["You've got this! Just a few more pieces!"],
            },
        }
        return tips_map.get(step_type, {}).get(tone, [])

    @staticmethod
    def _simple_step_svg(title: str, indices: List[int]) -> str:
        """Generate a simple SVG for a step."""
        labels = ", ".join(str(i) for i in indices)
        return (
            "<svg width='260' height='120' xmlns='http://www.w3.org/2000/svg'>"
            "<rect x='1' y='1' width='258' height='118' fill='white' stroke='#333'/>"
            f"<text x='14' y='28' font-size='14' font-family='Arial, sans-serif'>{title}</text>"
            f"<text x='14' y='54' font-size='12' font-family='Arial, sans-serif'>Parts: {labels}</text>"
            "</svg>"
        )
