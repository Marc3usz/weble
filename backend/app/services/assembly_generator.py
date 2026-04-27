"""Stage 4: Assembly Instruction Generation Service with Phase 3 LLM Support."""

import logging
from urllib.parse import quote
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
        if llm_service is not None:
            self.llm_service = llm_service
        elif settings.assembly_llm_enabled:
            try:
                from app.services.llm_assembly_generator import LLMAssemblyGeneratorService

                self.llm_service = LLMAssemblyGeneratorService()
            except Exception as e:
                self.logger.warning(f"Could not initialize LLM assembly generator: {e}")
                self.llm_service = None
        else:
            self.llm_service = None

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

        base_steps = await self._generate_rules_based_steps(parts, drawings, tone)

        # Try LLM if enabled and available
        if settings.assembly_llm_enabled and self.llm_service:
            try:
                self.logger.debug("Attempting LLM-based assembly generation...")
                steps = await self.llm_service.process(parts, drawings, tone, base_steps)
                # Add exploded views to each step
                from app.services.exploded_view_generator import ExplodedViewSVGGenerator

                svg_gen = ExplodedViewSVGGenerator()
                for step in steps:
                    step.exploded_view_svg = await svg_gen.generate_exploded_view(parts, step)
                    if step.exploded_view_svg:
                        step.svg_diagram = step.exploded_view_svg
                self.logger.info(f"Generated {len(steps)} steps using LLM")
                return steps
            except Exception as e:
                self.logger.warning(
                    f"LLM assembly generation failed ({e}), falling back to rules..."
                )
                # Fall through to rules-based generation

        # Rule-based fallback
        steps = base_steps

        # Add exploded views
        try:
            from app.services.exploded_view_generator import ExplodedViewSVGGenerator

            svg_gen = ExplodedViewSVGGenerator()
            for step in steps:
                step.exploded_view_svg = await svg_gen.generate_exploded_view(parts, step)
                if step.exploded_view_svg:
                    step.svg_diagram = step.exploded_view_svg
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

        semantic_panel_steps = self._generate_semantic_panel_steps(
            parts,
            panel_indices,
            connector_indices,
            tone,
        )
        if semantic_panel_steps:
            steps.extend(semantic_panel_steps)
            consumed_indices = {idx for step in steps for idx in step.part_indices}
            connector_indices = [idx for idx in connector_indices if idx not in consumed_indices]
            other_indices = [idx for idx in other_indices if idx not in consumed_indices]
            current_step = len(steps) + 1
            frame_indices = [idx for idx in panel_indices if idx not in consumed_indices]

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

        # Step 1..N: Interleaved frame + connector steps for practical build order
        if frame_indices:
            frame_chunk_size = 3
            frame_chunks = [
                frame_indices[i : i + frame_chunk_size]
                for i in range(0, len(frame_indices), frame_chunk_size)
            ]
            connector_chunk_size = 3
            connector_chunks = [
                connector_indices[i : i + connector_chunk_size]
                for i in range(0, len(connector_indices), connector_chunk_size)
            ]

            frame_context: List[int] = []
            for chunk_idx, active in enumerate(frame_chunks):
                title, desc, detail = self._get_step_text(tone, "frame")
                if len(frame_chunks) > 1:
                    title = f"{title} ({chunk_idx + 1}/{len(frame_chunks)})"

                active_roles = {
                    idx: self._role_for_part(parts[idx], "frame component") for idx in active
                }

                steps.append(
                    AssemblyStep(
                        step_number=current_step,
                        title=title,
                        description=self._build_step_description(parts, active, desc),
                        detail_description=self._build_step_detail(parts, active, detail),
                        part_indices=active,
                        part_roles=active_roles,
                        context_part_indices=frame_context.copy(),
                        assembly_sequence=["Align", "Secure"],
                        warnings=self._get_step_warnings(tone, "frame"),
                        tips=self._get_step_tips(tone, "frame"),
                        svg_diagram=self._simple_step_svg("Frame", active),
                        duration_minutes=6,
                        confidence_score=0.7,
                        is_llm_generated=False,
                    )
                )
                frame_context.extend(active)
                current_step += 1

                # Insert connector step right after each frame chunk when available
                if chunk_idx < len(connector_chunks):
                    conn_active = connector_chunks[chunk_idx]
                    conn_title, conn_desc, conn_detail = self._get_step_text(tone, "hardware")
                    if len(connector_chunks) > 1:
                        conn_title = f"{conn_title} ({chunk_idx + 1}/{len(connector_chunks)})"
                    conn_roles = {
                        idx: self._role_for_part(parts[idx], "connector") for idx in conn_active
                    }
                    steps.append(
                        AssemblyStep(
                            step_number=current_step,
                            title=conn_title,
                            description=self._build_step_description(parts, conn_active, conn_desc),
                            detail_description=self._build_step_detail(
                                parts, conn_active, conn_detail
                            ),
                            part_indices=conn_active,
                            part_roles=conn_roles,
                            context_part_indices=frame_context.copy(),
                            assembly_sequence=[
                                "Locate holes",
                                "Insert connector",
                                "Tighten lightly",
                            ],
                            warnings=self._get_step_warnings(tone, "hardware"),
                            tips=self._get_step_tips(tone, "hardware"),
                            svg_diagram=self._simple_step_svg("Hardware", conn_active),
                            duration_minutes=6,
                            confidence_score=0.7,
                            is_llm_generated=False,
                        )
                    )
                    frame_context.extend(conn_active)
                    current_step += 1

        # Remaining connectors not yet consumed
        consumed_connectors = {
            idx for step in steps for idx in step.part_indices if idx in connector_indices
        }
        remaining_connectors = [idx for idx in connector_indices if idx not in consumed_connectors]
        if remaining_connectors:
            title, desc, detail = self._get_step_text(tone, "hardware")
            active_roles = {
                idx: self._role_for_part(parts[idx], "connector") for idx in remaining_connectors
            }
            context = frame_indices + [
                idx for idx in connector_indices if idx in consumed_connectors
            ]
            steps.append(
                AssemblyStep(
                    step_number=current_step,
                    title=title,
                    description=self._build_step_description(parts, remaining_connectors, desc),
                    detail_description=self._build_step_detail(parts, remaining_connectors, detail),
                    part_indices=remaining_connectors,
                    part_roles=active_roles,
                    context_part_indices=context,
                    assembly_sequence=["Insert connector", "Tighten", "Verify joint"],
                    warnings=self._get_step_warnings(tone, "hardware"),
                    tips=self._get_step_tips(tone, "hardware"),
                    svg_diagram=self._simple_step_svg("Hardware", remaining_connectors),
                    duration_minutes=6,
                    confidence_score=0.7,
                    is_llm_generated=False,
                )
            )
            current_step += 1

        # Remaining components in chunks
        if other_indices:
            other_chunk_size = 4
            other_chunks = [
                other_indices[i : i + other_chunk_size]
                for i in range(0, len(other_indices), other_chunk_size)
            ]
            context = frame_indices + connector_indices
            for chunk_idx, active in enumerate(other_chunks):
                title, desc, detail = self._get_step_text(tone, "remaining")
                if len(other_chunks) > 1:
                    title = f"{title} ({chunk_idx + 1}/{len(other_chunks)})"

                active_roles = {
                    idx: self._role_for_part(parts[idx], "secondary component") for idx in active
                }
                steps.append(
                    AssemblyStep(
                        step_number=current_step,
                        title=title,
                        description=self._build_step_description(parts, active, desc),
                        detail_description=self._build_step_detail(parts, active, detail),
                        part_indices=active,
                        part_roles=active_roles,
                        context_part_indices=context.copy(),
                        assembly_sequence=["Mount", "Verify"],
                        warnings=self._get_step_warnings(tone, "remaining"),
                        tips=self._get_step_tips(tone, "remaining"),
                        svg_diagram=self._simple_step_svg("Finalize", active),
                        duration_minutes=6,
                        confidence_score=0.7,
                        is_llm_generated=False,
                    )
                )
                context.extend(active)
                current_step += 1

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

        for step in steps:
            step.svg_diagram = self._compose_step_svg_from_drawings(step, drawings)

        return steps

    def _generate_semantic_panel_steps(
        self,
        parts: List[Part],
        panel_indices: List[int],
        connector_indices: List[int],
        tone: AssemblyTone,
    ) -> List[AssemblyStep]:
        """Create a more furniture-like panel sequence when enough panels are present."""
        if len(panel_indices) < 4:
            return []

        role_map = self._infer_panel_roles(parts, panel_indices)
        if role_map.get("base") is None or not role_map.get("sides"):
            return []

        steps: List[AssemblyStep] = []
        step_number = 1

        frame_active = [role_map["base"], *role_map["sides"][:2]]
        frame_active = list(dict.fromkeys(frame_active))
        steps.append(
            AssemblyStep(
                step_number=step_number,
                title="Assemble cabinet frame",
                description=self._build_semantic_step_description(
                    "Position the base panel and attach the side panels to establish the main frame.",
                    frame_active,
                    role_map["labels"],
                ),
                detail_description=self._build_semantic_step_detail(
                    parts,
                    frame_active,
                    role_map["labels"],
                    "Keep the side panel edges flush with the base before tightening the first fasteners.",
                ),
                part_indices=frame_active,
                part_roles={idx: role_map["labels"][idx] for idx in frame_active},
                context_part_indices=[],
                assembly_sequence=[
                    "Position base panel",
                    "Align side panels",
                    "Secure frame corners",
                ],
                warnings=self._get_step_warnings(tone, "frame"),
                tips=self._get_step_tips(tone, "frame"),
                svg_diagram=self._simple_step_svg("Frame", frame_active),
                duration_minutes=8,
                confidence_score=0.8,
                is_llm_generated=False,
            )
        )
        step_number += 1

        upper_active = [*role_map.get("top", []), *role_map.get("shelves", [])]
        if upper_active:
            upper_active = list(dict.fromkeys(upper_active))
            steps.append(
                AssemblyStep(
                    step_number=step_number,
                    title="Install upper and internal panels",
                    description=self._build_semantic_step_description(
                        "Fit the upper or internal panels into the frame while keeping the cabinet square.",
                        upper_active,
                        role_map["labels"],
                    ),
                    detail_description=self._build_semantic_step_detail(
                        parts,
                        upper_active,
                        role_map["labels"],
                        "Seat each panel fully against the frame before moving to the next panel.",
                    ),
                    part_indices=upper_active,
                    part_roles={idx: role_map["labels"][idx] for idx in upper_active},
                    context_part_indices=frame_active.copy(),
                    assembly_sequence=["Place panel", "Check alignment", "Secure connection"],
                    warnings=self._get_step_warnings(tone, "remaining"),
                    tips=self._get_step_tips(tone, "remaining"),
                    svg_diagram=self._simple_step_svg("Panels", upper_active),
                    duration_minutes=6,
                    confidence_score=0.8,
                    is_llm_generated=False,
                )
            )
            step_number += 1

        back_panel = role_map.get("back")
        if back_panel is not None:
            context = [idx for step in steps for idx in step.part_indices]
            steps.append(
                AssemblyStep(
                    step_number=step_number,
                    title="Install back panel",
                    description=self._build_semantic_step_description(
                        "Square the cabinet frame, then attach the back panel to lock the geometry in place.",
                        [back_panel],
                        role_map["labels"],
                    ),
                    detail_description=self._build_semantic_step_detail(
                        parts,
                        [back_panel],
                        role_map["labels"],
                        "Confirm diagonal alignment before fixing the back panel along the rear edges.",
                    ),
                    part_indices=[back_panel],
                    part_roles={back_panel: role_map["labels"][back_panel]},
                    context_part_indices=context,
                    assembly_sequence=["Square frame", "Place back panel", "Fix rear perimeter"],
                    warnings=self._get_step_warnings(tone, "remaining"),
                    tips=self._get_step_tips(tone, "remaining"),
                    svg_diagram=self._simple_step_svg("Back", [back_panel]),
                    duration_minutes=5,
                    confidence_score=0.85,
                    is_llm_generated=False,
                )
            )
            step_number += 1

        if connector_indices:
            connector_labels = {
                idx: self._role_for_part(parts[idx], "fastener set") for idx in connector_indices
            }
            context = [idx for step in steps for idx in step.part_indices]
            steps.append(
                AssemblyStep(
                    step_number=step_number,
                    title="Final fastening pass",
                    description=self._build_semantic_step_description(
                        "Apply the remaining fasteners after the panel set is aligned.",
                        connector_indices,
                        connector_labels,
                    ),
                    detail_description=self._build_semantic_step_detail(
                        parts,
                        connector_indices,
                        connector_labels,
                        "Tighten the fasteners in stages so the frame remains square while the joints are fully seated.",
                    ),
                    part_indices=connector_indices,
                    part_roles=connector_labels,
                    context_part_indices=context,
                    assembly_sequence=[
                        "Locate fasteners",
                        "Tighten in sequence",
                        "Verify joint preload",
                    ],
                    warnings=self._get_step_warnings(tone, "hardware"),
                    tips=self._get_step_tips(tone, "hardware"),
                    svg_diagram=self._simple_step_svg("Fasteners", connector_indices),
                    duration_minutes=5,
                    confidence_score=0.8,
                    is_llm_generated=False,
                )
            )

        return steps

    def _infer_panel_roles(self, parts: List[Part], panel_indices: List[int]) -> dict:
        """Infer semantic roles for furniture-like panel sets."""
        panel_infos = []
        for idx in panel_indices:
            dims = parts[idx].dimensions or {}
            dims_sorted = sorted(
                [
                    float(dims.get("width", 0)),
                    float(dims.get("height", 0)),
                    float(dims.get("depth", 0)),
                ],
                reverse=True,
            )
            major = dims_sorted[0]
            mid = dims_sorted[1]
            thickness = dims_sorted[2]
            area = major * mid
            panel_infos.append(
                {
                    "idx": idx,
                    "major": major,
                    "mid": mid,
                    "thickness": thickness,
                    "area": area,
                }
            )

        panel_infos.sort(key=lambda item: item["area"], reverse=True)
        labels = {item["idx"]: "panel" for item in panel_infos}

        back_panel = None
        if len(panel_infos) >= 4:
            thinnest = min(panel_infos, key=lambda item: item["thickness"])
            second_thickness = sorted(item["thickness"] for item in panel_infos)[1]
            max_area = panel_infos[0]["area"]
            if (
                thinnest["thickness"] < second_thickness * 0.5
                and thinnest["area"] >= max_area * 0.55
            ):
                back_panel = thinnest["idx"]
                labels[back_panel] = "back panel"
                panel_infos = [item for item in panel_infos if item["idx"] != back_panel]

        if not panel_infos:
            return {"labels": labels, "sides": [], "top": [], "shelves": []}

        base_idx = panel_infos[0]["idx"]
        labels[base_idx] = "base panel"

        remaining = panel_infos[1:]
        side_candidates = [item["idx"] for item in remaining[:2]]
        for idx in side_candidates:
            labels[idx] = "side panel"

        remainder = [item["idx"] for item in remaining if item["idx"] not in side_candidates]
        top_panel = remainder[:1]
        if top_panel:
            labels[top_panel[0]] = "top panel"

        shelves = remainder[1:]
        for idx in shelves:
            labels[idx] = "shelf panel"

        return {
            "labels": labels,
            "base": base_idx,
            "sides": side_candidates,
            "top": top_panel,
            "shelves": shelves,
            "back": back_panel,
        }

    @staticmethod
    def _build_semantic_step_description(
        base: str, indices: List[int], role_map: dict[int, str]
    ) -> str:
        labels = [role_map.get(idx, str(idx)) for idx in indices]
        return f"{base} Czesci w tym kroku: {', '.join(labels)}."

    def _build_semantic_step_detail(
        self,
        parts: List[Part],
        indices: List[int],
        role_map: dict[int, str],
        base: str,
    ) -> str:
        details = []
        for idx in indices:
            if 0 <= idx < len(parts):
                dims = parts[idx].dimensions or {}
                details.append(
                    f"{role_map.get(idx, parts[idx].id)}: {dims.get('width', 0):.0f}×{dims.get('height', 0):.0f}×{dims.get('depth', 0):.0f}"
                )
        return f"{base} {'; '.join(details)}."

    # =========================================================================
    # TONE-SPECIFIC TEXT GENERATION
    # =========================================================================

    def _get_step_text(self, tone: AssemblyTone, step_type: str) -> tuple:
        """Get tone-appropriate title, description, and detail for a step type."""
        text_map = {
            "frame": {
                AssemblyTone.IKEA: (
                    "Assemble the main frame",
                    "Assemble the primary frame components",
                    "Align the frame pieces, verify edge contact, and secure the joints in the shown order.",
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
                    "Install the hardware",
                    "Install hardware components to secure the frame",
                    "Seat each hardware item fully, then tighten only after the connected parts remain aligned.",
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
                    "Install the remaining components",
                    "Attach the remaining components",
                    "Install the remaining components and verify that the previous joints stay seated during final positioning.",
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
                AssemblyTone.IKEA: [
                    "Verify that each frame joint is fully seated before moving to the next connection."
                ],
                AssemblyTone.TECHNICAL: ["Verify alignment and secure all joints"],
                AssemblyTone.BEGINNER: [
                    "Be very careful to align pieces before pushing them together"
                ],
            },
            "hardware": {
                AssemblyTone.IKEA: ["Do not over-tighten the hardware during initial seating."],
                AssemblyTone.TECHNICAL: ["Do not exceed specified torque limits"],
                AssemblyTone.BEGINNER: [
                    "WARNING: Don't make them too tight or you might break something"
                ],
            },
            "remaining": {
                AssemblyTone.IKEA: [
                    "Perform a final seating check after the last component is installed."
                ],
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
                AssemblyTone.IKEA: [
                    "Use a flat reference surface to confirm alignment before tightening."
                ],
                AssemblyTone.TECHNICAL: ["Use measuring instruments to verify alignment"],
                AssemblyTone.BEGINNER: ["It really helps to lay everything on a flat table"],
            },
            "hardware": {
                AssemblyTone.IKEA: [
                    "Tighten hardware in stages if several fasteners secure the same joint."
                ],
                AssemblyTone.TECHNICAL: ["Apply fasteners in a cross pattern if multiple"],
                AssemblyTone.BEGINNER: ["When something feels snug, stop - don't keep turning"],
            },
            "remaining": {
                AssemblyTone.IKEA: [
                    "Check the final assembly against the previous step before closing the sequence."
                ],
                AssemblyTone.TECHNICAL: ["Document final assembly state for reference"],
                AssemblyTone.BEGINNER: ["You've got this! Just a few more pieces!"],
            },
        }
        return tips_map.get(step_type, {}).get(tone, [])

    def _build_step_description(self, parts: List[Part], indices: List[int], base: str) -> str:
        names = [self._part_short_name(parts[idx]) for idx in indices if 0 <= idx < len(parts)]
        if not names:
            return base
        return f"{base}. Części w tym kroku: {', '.join(names)}."

    def _build_step_detail(self, parts: List[Part], indices: List[int], base: str) -> str:
        details = []
        for idx in indices:
            if 0 <= idx < len(parts):
                p = parts[idx]
                d = p.dimensions
                details.append(
                    f"{p.id}: {p.part_type.value} {d.get('width', 0):.0f}×{d.get('height', 0):.0f}×{d.get('depth', 0):.0f}"
                )
        if not details:
            return base
        return f"{base} {'; '.join(details)}."

    def _compose_step_svg_from_drawings(
        self, step: AssemblyStep, drawings: List[SvgDrawing]
    ) -> str:
        active = step.part_indices[:4]
        if not active:
            return self._simple_step_svg(step.title, step.part_indices)

        card_w = 220
        card_h = 160
        pad = 16
        cols = min(2, max(1, len(active)))
        rows = (len(active) + cols - 1) // cols
        width = cols * card_w + (cols + 1) * pad
        height = rows * card_h + (rows + 1) * pad + 34

        svg = [
            f"<svg width='{width}' height='{height}' xmlns='http://www.w3.org/2000/svg'>",
            f"<rect x='0' y='0' width='{width}' height='{height}' fill='white' stroke='#ddd'/>",
            f"<text x='{pad}' y='22' font-size='14' font-family='Arial' font-weight='bold'>{step.title}</text>",
        ]

        for i, idx in enumerate(active):
            if idx < 0 or idx >= len(drawings):
                continue
            x = pad + (i % cols) * (card_w + pad)
            y = 34 + pad + (i // cols) * (card_h + pad)
            part_svg = drawings[idx].svg_content
            data_uri = f"data:image/svg+xml;utf8,{quote(part_svg)}"
            svg.append(
                f"<rect x='{x}' y='{y}' width='{card_w}' height='{card_h}' fill='#fafafa' stroke='#bbb'/>"
            )
            svg.append(
                f"<image href=\"{data_uri}\" x='{x + 4}' y='{y + 4}' width='{card_w - 8}' height='{card_h - 8}' preserveAspectRatio='xMidYMid meet' />"
            )

        svg.append("</svg>")
        return "".join(svg)

    @staticmethod
    def _part_short_name(part: Part) -> str:
        d = part.dimensions
        return f"{part.part_type.value} {d.get('width', 0):.0f}×{d.get('height', 0):.0f}×{d.get('depth', 0):.0f}"

    @staticmethod
    def _role_for_part(part: Part, fallback: str) -> str:
        """Create a more informative role label from part metadata."""
        dims = part.dimensions or {}
        w = float(dims.get("width", 0))
        h = float(dims.get("height", 0))
        d = float(dims.get("depth", 0))

        dims_sorted = sorted([w, h, d], reverse=True)
        longest = dims_sorted[0] if dims_sorted else 0
        shortest = dims_sorted[-1] if dims_sorted else 0

        label = part.part_type.value
        if longest > 0 and shortest > 0 and (longest / max(shortest, 1e-6)) > 4:
            label = f"{label} panel"

        return f"{label} ({w:.0f}×{h:.0f}×{d:.0f})" if w and h and d else fallback

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
