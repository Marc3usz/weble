"""LLM-powered Assembly Instruction Generator (Phase 3).

Generates human-readable assembly instructions using OpenRouter API with Google Gemini.
Includes fallback to rule-based generation if LLM unavailable.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx
from pydantic import ValidationError

from app.core.config import AssemblyTone, settings
from app.core.exceptions import CADProcessingError, LLMApiError
from app.models.schemas import AssemblyStep, LLMAssemblyResponse, Part, PartType, SvgDrawing


logger = logging.getLogger(__name__)


class LLMAssemblyGeneratorService:
    """Generate assembly instructions using LLM with fallback to rules."""

    def __init__(self):
        """Initialize LLM service."""
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        self.model = settings.assembly_llm_model
        self.timeout = settings.llm_timeout_seconds
        self.max_tokens = settings.llm_max_tokens

    # =========================================================================
    # PUBLIC INTERFACE
    # =========================================================================

    async def validate_input(
        self, parts: List[Part], drawings: List[SvgDrawing]
    ) -> Tuple[bool, Optional[str]]:
        """Validate input parts and drawings.

        Args:
            parts: List of Part objects
            drawings: List of SvgDrawing objects

        Returns:
            (is_valid, error_message)
        """
        # Check empty
        if not parts:
            return False, "Parts list cannot be empty"
        if not drawings:
            return False, "Drawings list cannot be empty"

        # Check count mismatch
        if len(parts) != len(drawings):
            return (
                False,
                f"Parts and drawings count mismatch: {len(parts)} parts vs {len(drawings)} drawings",
            )

        # Check required fields in parts
        for part in parts:
            if not hasattr(part, "id") or not part.id:
                return False, "Part missing required field: id"
            if not hasattr(part, "part_type"):
                return False, f"Part {part.id} missing required field: part_type"
            if not hasattr(part, "volume"):
                return False, f"Part {part.id} missing required field: volume"
            if not hasattr(part, "dimensions"):
                return False, f"Part {part.id} missing required field: dimensions"
            if not hasattr(part, "centroid"):
                return False, f"Part {part.id} missing required field: centroid"

        return True, None

    async def process(
        self,
        parts: List[Part],
        drawings: List[SvgDrawing],
        tone: AssemblyTone = AssemblyTone.IKEA,
        base_steps: Optional[List[AssemblyStep]] = None,
    ) -> List[AssemblyStep]:
        """Generate assembly instructions using LLM or fallback to rules.

        Args:
            parts: List of parts to assemble
            drawings: List of SVG drawings for parts
            tone: Assembly instruction tone (IKEA, TECHNICAL, BEGINNER)

        Returns:
            List of AssemblyStep objects with LLM-generated instructions

        Raises:
            PipelineStageError: If both LLM and fallback fail
        """
        # Validate input
        is_valid, error = await self.validate_input(parts, drawings)
        if not is_valid:
            raise PipelineStageError(f"Invalid input: {error}")

        # Try LLM if enabled
        if settings.openrouter_api_key and settings.assembly_llm_enabled:
            try:
                logger.info("Attempting LLM-based assembly generation...")
                steps = await self._generate_llm_instructions(parts, drawings, tone, base_steps)
                logger.info(f"Successfully generated {len(steps)} steps using LLM")
                return steps
            except LLMApiError as e:
                logger.warning(f"LLM failed ({e}), falling back to rule-based generation")
                # Fall through to fallback
            except Exception as e:
                logger.error(f"Unexpected error during LLM generation: {e}")
                # Fall through to fallback

        # Fallback to rules-based generation
        logger.info("Using rule-based assembly generation")
        return await self._generate_rules_based_instructions(parts, drawings, tone)

    # =========================================================================
    # LLM GENERATION PIPELINE
    # =========================================================================

    async def _generate_llm_instructions(
        self,
        parts: List[Part],
        drawings: List[SvgDrawing],
        tone: AssemblyTone,
        base_steps: Optional[List[AssemblyStep]] = None,
    ) -> List[AssemblyStep]:
        """Generate instructions using LLM.

        Args:
            parts: List of parts
            drawings: List of drawings
            tone: Assembly tone

        Returns:
            List of AssemblyStep objects

        Raises:
            LLMApiError: If API call fails
        """
        # Build prompt
        prompt = await self._build_prompt(parts, drawings, tone, base_steps)
        logger.debug(f"Prompt length: {len(prompt)} chars, ~{len(prompt) // 4} tokens")

        # Call API
        response_text = await self._call_openrouter_api(prompt)

        # Parse response
        steps = await self._parse_llm_response(response_text, base_steps)

        return steps

    async def _build_prompt(
        self,
        parts: List[Part],
        drawings: List[SvgDrawing],
        tone: AssemblyTone,
        base_steps: Optional[List[AssemblyStep]] = None,
    ) -> str:
        """Build LLM prompt from parts and drawings.

        Args:
            parts: List of parts
            drawings: List of SVG drawings
            tone: Assembly instruction tone

        Returns:
            Formatted prompt string
        """
        # System message
        system_message = self._get_system_message(tone)

        # Parts context
        parts_context = await self._build_parts_context(parts, drawings)

        # Output format specification
        output_format = self._get_output_format_spec()

        # Optional predefined step skeleton
        step_skeleton = self._build_step_skeleton_context(base_steps)

        # Guardrails
        constraints = self._get_generation_constraints(base_steps)

        # Few-shot examples
        examples = self._get_tone_examples(tone)

        # Combine prompt
        prompt = f"""{system_message}

## Assembly Context

{parts_context}

## Step Skeleton

{step_skeleton}

## Constraints

{constraints}

## Output Format Specification

{output_format}

## Examples

{examples}

## Your Task

Rewrite the predefined assembly steps into precise technical instructions for the parts listed above.
Produce valid JSON that matches the specification exactly.
"""
        return prompt

    def _build_step_skeleton_context(self, base_steps: Optional[List[AssemblyStep]]) -> str:
        """Serialize predefined steps for constrained enrichment."""
        if not base_steps:
            return "No predefined step skeleton was provided. Infer a practical sequence from the parts list."

        skeleton: List[Dict[str, Any]] = []
        for step in base_steps:
            skeleton.append(
                {
                    "step_number": step.step_number,
                    "title": step.title,
                    "part_indices": step.part_indices,
                    "context_part_indices": step.context_part_indices,
                    "part_roles": {str(key): value for key, value in step.part_roles.items()},
                    "duration_minutes": step.duration_minutes,
                }
            )

        return json.dumps({"steps": skeleton}, indent=2)

    def _get_generation_constraints(self, base_steps: Optional[List[AssemblyStep]]) -> str:
        """Return hard constraints that reduce hallucinations."""
        constraints = [
            "Use a technical and concise tone.",
            "Do not mention tools, fasteners, fittings, tolerances, or measurements unless they are present in the provided data.",
            "Do not use emoji, excitement, marketing language, or conversational filler.",
            "Keep description to one or two short operational sentences.",
            "Only include warnings or tips when they are justified by the parts or assembly context.",
        ]
        if base_steps:
            constraints.extend(
                [
                    "Do not change step_number.",
                    "Do not change part_indices.",
                    "Do not change context_part_indices.",
                    "Keep the same number of steps as the predefined skeleton.",
                ]
            )
        return "\n".join(f"- {item}" for item in constraints)

    def _get_system_message(self, tone: AssemblyTone) -> str:
        """Get system message for tone."""
        if tone == AssemblyTone.IKEA:
            return """You are an expert technical assembly writer. Create assembly instructions that are:
- Concise and operational
- Grounded in the provided assembly data only
- Focused on alignment, fit, order, and fastening accuracy
- Free of marketing language, emoji, and unnecessary encouragement
- Suitable for a manufacturing or workshop assembly sheet"""

        elif tone == AssemblyTone.TECHNICAL:
            return """You are a technical documentation expert. Create assembly instructions that are:
- Precise and formal
- Use technical terminology appropriately
- Include exact specifications and tolerances
- Focus on accuracy and correctness
- Suitable for engineers and technical users"""

        else:  # BEGINNER
            return """You are a careful technical instructor. Create assembly instructions that are:
- Detailed and step-by-step
- Focused on alignment, safety, and common mistakes
- Written in simple but still technical language
- Free of filler, hype, and invented details"""

    async def _build_parts_context(
        self,
        parts: List[Part],
        drawings: List[SvgDrawing],
    ) -> str:
        """Build detailed context about parts from metadata and drawings."""
        context_lines = []

        for part, drawing in zip(parts, drawings):
            # Part header
            context_lines.append(f"**Part {part.id}** ({part.part_type.value})")

            # Dimensions
            dims = part.dimensions
            context_lines.append(
                f"  - Dimensions: {dims.get('width', 0):.1f}×{dims.get('height', 0):.1f}×{dims.get('depth', 0):.1f} mm"
            )

            # Volume
            context_lines.append(f"  - Volume: {part.volume:.1f} mm³")

            # Quantity
            if part.quantity > 1:
                context_lines.append(f"  - Quantity: {part.quantity} identical parts")

            # Drawing metadata
            if drawing.metadata:
                if "projection" in drawing.metadata:
                    context_lines.append(f"  - Visual: {drawing.metadata['projection']}")
                if "includes" in drawing.metadata:
                    views = ", ".join(drawing.metadata["includes"])
                    context_lines.append(f"  - Views: {views}")

        return "\n".join(context_lines)

    def _get_output_format_spec(self) -> str:
        """Get JSON output format specification."""
        return """{
  "steps": [
    {
      "step_number": <int>,
      "title": "<step title, action-focused>",
      "description": "<concise description>",
      "detail_description": "<detailed explanation with why/how>",
      "part_indices": [<indices of parts involved>],
      "part_roles": {<"0": "role_of_part_0", ...>},
      "context_part_indices": [<indices of reference/support parts>],
      "assembly_sequence": ["<action1>", "<action2>", ...],
      "warnings": ["<safety_warning_if_applicable>"],
      "tips": ["<helpful_tip_if_applicable>"],
      "duration_minutes": <estimated_time>
    }
  ]
}"""

    def _get_tone_examples(self, tone: AssemblyTone) -> str:
        """Get few-shot examples for the tone."""
        if tone == AssemblyTone.IKEA:
            return """{
  "steps": [
    {
      "step_number": 1,
      "title": "Snap the frame pieces together",
      "description": "Connect the left and right frame sides",
      "detail_description": "Take the two main frame pieces and align the connecting slots. They'll click together with a satisfying snap!",
      "part_indices": [0, 1],
      "part_roles": {"0": "left frame", "1": "right frame"},
      "assembly_sequence": ["Align slots", "Press together"],
      "warnings": [],
      "tips": ["Make sure the slots face each other before pressing"],
      "duration_minutes": 3
    }
  ]
}"""

        elif tone == AssemblyTone.TECHNICAL:
            return """{
  "steps": [
    {
      "step_number": 1,
      "title": "Assemble main frame structure",
      "description": "Secure primary structural components",
      "detail_description": "Position frame components A and B with alignment tolerance ±2mm. Ensure orthogonal alignment before fastening.",
      "part_indices": [0, 1],
      "part_roles": {"0": "left frame", "1": "right frame"},
      "assembly_sequence": ["Position", "Align", "Secure"],
      "warnings": ["Maintain 90-degree angles"],
      "tips": ["Use alignment fixtures for precision"],
      "duration_minutes": 5
    }
  ]
}"""

        else:  # BEGINNER
            return """{
  "steps": [
    {
      "step_number": 1,
      "title": "Connect the two frame sides (super easy!)",
      "description": "Link the left and right frame pieces together",
      "detail_description": "Find the two big frame pieces (left and right). Look for the connecting slots on each piece - they look like grooves. Carefully push them together until they click. Don't force it!",
      "part_indices": [0, 1],
      "part_roles": {"0": "left side frame", "1": "right side frame"},
      "assembly_sequence": ["Find the slots", "Align the pieces", "Gently press together"],
      "warnings": ["Be careful not to pinch fingers when pressing"],
      "tips": ["If it's hard to push, check that the slots are facing each other"],
      "duration_minutes": 3
    }
  ]
}"""

    async def _call_openrouter_api(self, prompt: str) -> str:
        """Call OpenRouter API with prompt.

        Args:
            prompt: Formatted prompt string

        Returns:
            Response content from LLM

        Raises:
            LLMApiError: If API call fails
        """
        if not self.api_key:
            raise LLMApiError(500, "OpenRouter API key not configured (set OPENROUTER_API_KEY)")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": self.max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )

                # Handle HTTP errors
                if response.status_code == 401:
                    raise LLMApiError(401, "Authentication failed: Check OPENROUTER_API_KEY")
                elif response.status_code == 429:
                    raise LLMApiError(429, "Rate limited: Too many requests, retry later")
                elif response.status_code >= 400:
                    raise LLMApiError(response.status_code, f"API error: {response.text[:200]}")

                # Extract response
                response_data = response.json()
                if "choices" not in response_data or not response_data["choices"]:
                    raise LLMApiError(500, f"Invalid response format: {response_data}")

                content = response_data["choices"][0]["message"]["content"]
                return content

        except asyncio.TimeoutError:
            raise LLMApiError(504, f"API timeout: request exceeded {self.timeout}s")
        except httpx.RequestError as e:
            raise LLMApiError(500, f"Request error: {e}")
        except json.JSONDecodeError as e:
            raise LLMApiError(500, f"Invalid JSON response: {e}")

    async def _parse_llm_response(
        self,
        response_text: str,
        expected_steps: Optional[List[AssemblyStep]] = None,
    ) -> List[AssemblyStep]:
        """Parse LLM response into AssemblyStep objects.

        Args:
            response_text: Raw response from LLM

        Returns:
            List of AssemblyStep objects

        Raises:
            ValidationError: If response doesn't match expected format
        """
        try:
            # Extract JSON from response (may contain markdown code blocks)
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith("```"):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith("```"):
                response_text = response_text[:-3]  # Remove trailing ```

            # Parse JSON
            response_data = json.loads(response_text)

            # Extract steps
            if "steps" not in response_data:
                self._raise_validation_error("Response missing 'steps' field")

            steps = []
            for step_data in response_data["steps"]:
                step = self._create_assembly_step_from_llm(step_data)
                steps.append(step)

            if not steps:
                self._raise_validation_error("Response contains no steps")

            self._validate_enriched_steps(steps, expected_steps)

            return steps

        except json.JSONDecodeError as e:
            self._raise_validation_error(f"Invalid JSON in response: {e}")

    def _validate_enriched_steps(
        self,
        steps: List[AssemblyStep],
        expected_steps: Optional[List[AssemblyStep]],
    ) -> None:
        """Validate that enriched steps preserve the predefined topology."""
        if not expected_steps:
            return

        if len(steps) != len(expected_steps):
            self._raise_validation_error("LLM response changed the number of assembly steps")

        for actual, expected in zip(steps, expected_steps):
            if actual.step_number != expected.step_number:
                self._raise_validation_error(
                    f"LLM response changed step_number for step {expected.step_number}"
                )
            if actual.part_indices != expected.part_indices:
                self._raise_validation_error(
                    f"LLM response changed part_indices for step {expected.step_number}"
                )
            if actual.context_part_indices != expected.context_part_indices:
                self._raise_validation_error(
                    f"LLM response changed context_part_indices for step {expected.step_number}"
                )
            if not actual.description.strip() or len(actual.description.strip()) < 10:
                self._raise_validation_error(
                    f"LLM response returned an incomplete description for step {expected.step_number}"
                )
            if any(
                token in actual.description.lower()
                for token in ["thing", "stuff", "component together"]
            ):
                self._raise_validation_error(
                    f"LLM response returned generic wording for step {expected.step_number}"
                )

    def _raise_validation_error(self, message: str) -> None:
        """Raise a pydantic validation error with a simple message."""
        raise ValidationError.from_exception_data(
            "LLMAssemblyResponse",
            [
                {
                    "type": "value_error",
                    "loc": ("steps",),
                    "msg": message,
                    "input": None,
                    "ctx": {"error": ValueError(message)},
                }
            ],
        )

    def _create_assembly_step_from_llm(self, step_data: dict) -> AssemblyStep:
        """Create AssemblyStep from LLM response data.

        Args:
            step_data: Dictionary with step information

        Returns:
            AssemblyStep object with is_llm_generated=True
        """
        return AssemblyStep(
            step_number=step_data.get("step_number", 1),
            title=step_data.get("title", "Assembly step"),
            description=step_data.get("description", ""),
            detail_description=step_data.get(
                "detail_description", step_data.get("description", "")
            ),
            part_indices=step_data.get("part_indices", []),
            part_roles=step_data.get("part_roles", {}),
            context_part_indices=step_data.get("context_part_indices", []),
            assembly_sequence=step_data.get("assembly_sequence", []),
            warnings=step_data.get("warnings", []),
            tips=step_data.get("tips", []),
            duration_minutes=step_data.get("duration_minutes", 5),
            confidence_score=step_data.get("confidence_score", 0.9),
            is_llm_generated=True,
        )

    # =========================================================================
    # FALLBACK: RULE-BASED GENERATION
    # =========================================================================

    async def _generate_rules_based_instructions(
        self,
        parts: List[Part],
        drawings: List[SvgDrawing],
        tone: AssemblyTone,
    ) -> List[AssemblyStep]:
        """Generate instructions using rules when LLM unavailable.

        Args:
            parts: List of parts
            drawings: List of drawings (unused in rules)
            tone: Assembly tone (affects language style)

        Returns:
            List of AssemblyStep objects with is_llm_generated=False
        """
        # Group parts by type
        structural = [p for p in parts if p.part_type == PartType.STRUCTURAL]
        hardware = [p for p in parts if p.part_type == PartType.HARDWARE]
        fasteners = [p for p in parts if p.part_type == PartType.FASTENER]
        panels = [p for p in parts if p.part_type == PartType.PANEL]

        steps = []
        step_number = 1

        # Step 1: Structural assembly
        if structural:
            step = AssemblyStep(
                step_number=step_number,
                title=self._get_tone_text(tone, "assemble_structure"),
                description=f"Assembly of {len(structural)} structural component(s)",
                detail_description=self._get_tone_detail(
                    tone, f"assemble {len(structural)} structural part(s)"
                ),
                part_indices=[parts.index(p) for p in structural],
                part_roles={str(parts.index(p)): "structural component" for p in structural},
                context_part_indices=[],
                assembly_sequence=["Position", "Align", "Secure"],
                warnings=self._get_tone_warnings(tone, "structural"),
                tips=self._get_tone_tips(tone, "alignment"),
                duration_minutes=5 + len(structural),
                confidence_score=0.7,
                is_llm_generated=False,
            )
            steps.append(step)
            step_number += 1

        # Step 2: Panel installation
        if panels:
            step = AssemblyStep(
                step_number=step_number,
                title=self._get_tone_text(tone, "install_panels"),
                description=f"Installation of {len(panels)} panel(s)",
                detail_description=self._get_tone_detail(tone, f"attach {len(panels)} panel(s)"),
                part_indices=[parts.index(p) for p in panels],
                part_roles={str(parts.index(p)): "panel" for p in panels},
                context_part_indices=[parts.index(p) for p in structural] if structural else [],
                assembly_sequence=["Position", "Align", "Attach"],
                warnings=self._get_tone_warnings(tone, "panel"),
                tips=self._get_tone_tips(tone, "careful_handling"),
                duration_minutes=3 + len(panels),
                confidence_score=0.7,
                is_llm_generated=False,
            )
            steps.append(step)
            step_number += 1

        # Step 3: Hardware installation
        if hardware:
            step = AssemblyStep(
                step_number=step_number,
                title=self._get_tone_text(tone, "attach_hardware"),
                description=f"Installation of {len(hardware)} hardware component(s)",
                detail_description=self._get_tone_detail(
                    tone, f"install {len(hardware)} hardware part(s)"
                ),
                part_indices=[parts.index(p) for p in hardware],
                part_roles={str(parts.index(p)): "hardware" for p in hardware},
                context_part_indices=[parts.index(p) for p in structural + panels],
                assembly_sequence=["Position", "Secure"],
                warnings=self._get_tone_warnings(tone, "hardware"),
                tips=self._get_tone_tips(tone, "secure"),
                duration_minutes=3 + len(hardware),
                confidence_score=0.7,
                is_llm_generated=False,
            )
            steps.append(step)
            step_number += 1

        # Step 4: Fasteners
        if fasteners:
            step = AssemblyStep(
                step_number=step_number,
                title=self._get_tone_text(tone, "fasten"),
                description=f"Fastening with {len(fasteners)} fastener(s)",
                detail_description=self._get_tone_detail(
                    tone, f"secure with {len(fasteners)} fastener(s)"
                ),
                part_indices=[parts.index(p) for p in fasteners],
                part_roles={str(parts.index(p)): "fastener" for p in fasteners},
                context_part_indices=[parts.index(p) for p in structural + panels + hardware],
                assembly_sequence=["Position", "Tighten"],
                warnings=self._get_tone_warnings(tone, "fastener"),
                tips=self._get_tone_tips(tone, "not_too_tight"),
                duration_minutes=2 + len(fasteners),
                confidence_score=0.7,
                is_llm_generated=False,
            )
            steps.append(step)

        # If only 1 part, provide special step
        if len(parts) == 1:
            steps = [
                AssemblyStep(
                    step_number=1,
                    title="Part ready for use",
                    description="No assembly required",
                    detail_description=self._get_tone_detail(tone, "part is complete as-is"),
                    part_indices=[0],
                    part_roles={"0": "complete assembly"},
                    context_part_indices=[],
                    assembly_sequence=[],
                    warnings=[],
                    tips=[],
                    duration_minutes=0,
                    confidence_score=0.9,
                    is_llm_generated=False,
                )
            ]

        return steps

    def _get_tone_text(self, tone: AssemblyTone, key: str) -> str:
        """Get tone-appropriate text for a key."""
        tone_map = {
            AssemblyTone.IKEA: {
                "assemble_structure": "Assemble the main structure",
                "install_panels": "Install the panels",
                "attach_hardware": "Install the hardware",
                "fasten": "Secure the assembly with fasteners",
            },
            AssemblyTone.TECHNICAL: {
                "assemble_structure": "Assemble structural components",
                "install_panels": "Install panel elements",
                "attach_hardware": "Attach hardware components",
                "fasten": "Apply fastening elements",
            },
            AssemblyTone.BEGINNER: {
                "assemble_structure": "Build the main frame (take your time!)",
                "install_panels": "Carefully attach the panels",
                "attach_hardware": "Add the hardware pieces (be gentle)",
                "fasten": "Tighten the fasteners (not too tight!)",
            },
        }
        return tone_map.get(tone, {}).get(key, f"Step: {key}")

    def _get_tone_detail(self, tone: AssemblyTone, action: str) -> str:
        """Get tone-appropriate detail description."""
        if tone == AssemblyTone.IKEA:
            return f"{action.capitalize()}. Verify alignment and seating before proceeding to the next connection."
        elif tone == AssemblyTone.TECHNICAL:
            return (
                f"Proceed to {action}. Ensure all components are properly positioned and secured."
            )
        else:  # BEGINNER
            return f"Now we'll {action}. Don't worry if it seems tricky - follow along step by step. It's easier than it looks!"

    def _get_tone_warnings(self, tone: AssemblyTone, context: str) -> List[str]:
        """Get tone-appropriate warnings."""
        warnings_map = {
            "structural": {
                AssemblyTone.IKEA: [
                    "Confirm that all structural faces sit flush before securing the joint."
                ],
                AssemblyTone.TECHNICAL: ["Ensure orthogonal alignment"],
                AssemblyTone.BEGINNER: [
                    "Be very careful the parts are aligned before you push them together"
                ],
            },
            "panel": {
                AssemblyTone.IKEA: ["Support the panel fully while seating it into position."],
                AssemblyTone.TECHNICAL: ["Verify panel flatness and alignment"],
                AssemblyTone.BEGINNER: ["Be gentle with the panels - they're delicate"],
            },
            "hardware": {
                AssemblyTone.IKEA: [
                    "Check that each hardware item is fully seated before loading the joint."
                ],
                AssemblyTone.TECHNICAL: ["Ensure hardware components are properly seated"],
                AssemblyTone.BEGINNER: ["Make sure hardware pieces are sitting correctly"],
            },
            "fastener": {
                AssemblyTone.IKEA: ["Do not over-tighten the fasteners."],
                AssemblyTone.TECHNICAL: ["Tighten to specification - do not exceed torque limits"],
                AssemblyTone.BEGINNER: [
                    "WARNING: Don't make them too tight or you might strip them"
                ],
            },
        }
        return warnings_map.get(context, {}).get(tone, [])

    def _get_tone_tips(self, tone: AssemblyTone, context: str) -> List[str]:
        """Get tone-appropriate tips."""
        tips_map = {
            "alignment": {
                AssemblyTone.IKEA: [
                    "Use a flat reference surface to confirm alignment.",
                    "Check both edges before tightening the joint fully.",
                ],
                AssemblyTone.TECHNICAL: [
                    "Use measuring instruments for precision",
                    "Verify alignment with appropriate tools",
                ],
                AssemblyTone.BEGINNER: [
                    "It really helps to lay everything on a flat table",
                    "Double-check that pieces line up before moving on",
                ],
            },
            "careful_handling": {
                AssemblyTone.IKEA: [
                    "Support large panel faces to avoid edge damage during positioning."
                ],
                AssemblyTone.TECHNICAL: ["Handle with care to avoid damage"],
                AssemblyTone.BEGINNER: ["Be very gentle - if you drop it, it could break"],
            },
            "secure": {
                AssemblyTone.IKEA: [
                    "Verify that the joint is seated before applying final tightening."
                ],
                AssemblyTone.TECHNICAL: ["Verify all components are securely seated"],
                AssemblyTone.BEGINNER: ["Give everything a gentle tug - nothing should wiggle"],
            },
            "not_too_tight": {
                AssemblyTone.IKEA: ["Tighten until seated, then stop once resistance increases."],
                AssemblyTone.TECHNICAL: ["Tighten sufficiently but avoid over-tightening"],
                AssemblyTone.BEGINNER: ["When something feels snug, stop - don't keep turning"],
            },
        }
        return tips_map.get(context, {}).get(tone, [])

    # =========================================================================
    # TEST-COMPATIBLE WRAPPER METHODS
    # =========================================================================

    def _build_system_prompt(self, tone: AssemblyTone) -> str:
        """Build system prompt for the given tone. Wrapper for tests."""
        return self._get_system_message(tone)

    def _build_user_prompt(self, parts: List[Part], tone: AssemblyTone) -> str:
        """Build user prompt with parts information. Wrapper for tests."""
        # Build parts context synchronously (no drawings needed for tests)
        context_lines = []
        for part in parts:
            context_lines.append(f"**Part {part.id}** ({part.part_type.value})")
            dims = part.dimensions
            context_lines.append(
                f"  - Dimensions: {dims.get('width', 0):.1f}×{dims.get('height', 0):.1f}×{dims.get('depth', 0):.1f} mm"
            )
            context_lines.append(f"  - Volume: {part.volume:.1f} mm³")
            if part.quantity > 1:
                context_lines.append(f"  - Quantity: {part.quantity} identical parts")

        context = "\n".join(context_lines)
        examples = self._get_tone_examples(tone)
        format_spec = self._get_output_format_spec()

        return f"""# Assembly Task

## Parts to Assemble

{context}

## Output Format

{format_spec}

## Examples for Reference

{examples}

## Your Task

Generate detailed assembly instructions for assembling these parts.
"""

    def _estimate_tokens(self, parts: List[Part]) -> int:
        """Estimate tokens needed for assembling given parts."""
        # Rough estimation: ~100 tokens base + ~50 per part + ~30 per dimension value
        base_tokens = 100
        per_part_tokens = 50
        dimension_tokens = sum(len(part.dimensions) * 30 for part in parts)
        return base_tokens + (len(parts) * per_part_tokens) + dimension_tokens

    def _calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str = "google/gemini-2.0-flash",
    ) -> float:
        """Calculate estimated cost for LLM call."""
        # Gemini 2.0 Flash pricing (approximate):
        # Input: $0.10 per 1M tokens
        # Output: $0.40 per 1M output tokens
        input_cost = (prompt_tokens / 1_000_000) * 0.10
        output_cost = (completion_tokens / 1_000_000) * 0.40
        return input_cost + output_cost

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        tone: AssemblyTone,
        max_tokens: int = 2000,
    ) -> dict:
        """Call LLM API with given prompts. Wrapper for tests."""
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                )
                # Check status code before calling raise_for_status
                if response.status_code == 401:
                    raise LLMApiError(401, "Unauthorized - check API key")
                elif response.status_code == 429:
                    raise LLMApiError(429, "Rate limited - too many requests")
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as e:
            raise TimeoutError(f"LLM API request timed out: {e}")
        except LLMApiError:
            raise  # Re-raise LLMApiError as-is
        except httpx.HTTPError as e:
            raise LLMApiError(500, f"LLM API error: {e}")

    def _parse_response(self, response_text: str) -> List[AssemblyStep]:
        """Parse LLM response and convert to AssemblyStep objects."""
        import re

        # Try to extract JSON from response
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in LLM response")

        json_str = json_match.group(0)
        data = json.loads(json_str)

        steps = []
        for step_data in data.get("steps", []):
            step = self._create_assembly_step_from_llm(step_data)
            steps.append(step)

        return steps


# ============================================================================
# STANDALONE HELPERS
# ============================================================================


def estimate_tokens(text: str) -> int:
    """Rough estimate of token count (1 token ≈ 4 characters)."""
    return len(text) // 4


def estimate_cost(tokens_used: int, model: str = "google/gemini-2.0-flash") -> float:
    """Estimate cost based on tokens and model.

    Approximate rates (2024):
    - Gemini 2.0 Flash: $0.10 per 1M input tokens, $0.40 per 1M output tokens
    """
    input_tokens = tokens_used
    output_tokens = int(tokens_used * 0.5)  # Rough estimate: output is ~50% of input

    input_cost = (input_tokens / 1_000_000) * 0.10
    output_cost = (output_tokens / 1_000_000) * 0.40

    return input_cost + output_cost
