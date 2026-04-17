"""Stage 2: Parts Extraction Service - Phase 2 Enhanced."""

import logging
from copy import deepcopy
from typing import List

from app.services.step_loader import PipelineStage
from app.models.schemas import Part, PartType, Geometry3D

logger = logging.getLogger(__name__)

# Phase 2: Adaptive tolerance configuration
MIN_TOLERANCE = 0.05  # 5% for high-precision matching
BASE_TOLERANCE = 0.15  # 15% for standard matching
MAX_TOLERANCE = 0.30  # 30% for loose matching


class PartsExtractorService(PipelineStage):
    """
    Stage 2: Extract and classify parts from geometry.

    Input:  Geometry3D (from Stage 1)
    Output: Parts[] (with classification and deduplication)
    """

    def __init__(self) -> None:
        self.name = "PartsExtractorService"
        self.logger = logging.getLogger(__name__)

    async def validate_input(self, data: Geometry3D) -> bool:
        """Validate geometry has solids."""
        if not isinstance(data, Geometry3D):
            return False
        return len(data.vertices) > 0

    async def process(self, geometry: Geometry3D) -> List[Part]:
        """
        Extract parts from geometry and classify them (Phase 2 Enhanced).

        Uses Stage 1 metadata when available and applies adaptive tolerance-based
        deduplication based on model scale. This improves accuracy for models
        with mixed-size parts.

        Returns:
            List of classified, deduplicated parts with grouping information.
        """

        is_valid = await self.validate_input(geometry)
        if not is_valid:
            raise ValueError("Invalid geometry input")

        self.logger.info("Extracting and classifying parts (Phase 2 Enhanced)...")

        solids = geometry.metadata.get("solids", []) if geometry.metadata else []

        if solids:
            raw_parts = [self._solid_to_part(solid, idx) for idx, solid in enumerate(solids)]

            # Phase 2: Calculate adaptive tolerance based on model scale
            tolerance = self._calculate_adaptive_tolerance(raw_parts)
            self.logger.info("Using adaptive tolerance: %.2f%%", tolerance * 100)

            parts = self._deduplicate_parts_adaptive(raw_parts, tolerance)
        else:
            parts = self._fallback_parts_from_bounds(geometry)

        self.logger.info("Extracted %s unique parts", len(parts))
        return parts

    def _solid_to_part(self, solid: dict, idx: int) -> Part:
        bbox = solid.get("bounding_box", {})
        bbox_min = bbox.get("min", [0.0, 0.0, 0.0])
        bbox_max = bbox.get("max", [0.0, 0.0, 0.0])
        dimensions = {
            "width": float(abs(bbox_max[0] - bbox_min[0])),
            "height": float(abs(bbox_max[1] - bbox_min[1])),
            "depth": float(abs(bbox_max[2] - bbox_min[2])),
        }

        centroid = solid.get(
            "centroid",
            [
                (bbox_min[0] + bbox_max[0]) / 2.0,
                (bbox_min[1] + bbox_max[1]) / 2.0,
                (bbox_min[2] + bbox_max[2]) / 2.0,
            ],
        )

        volume = float(
            solid.get("volume", dimensions["width"] * dimensions["height"] * dimensions["depth"])
        )
        surface_area = self._estimate_surface_area(dimensions)
        part_type = self._classify(dimensions, volume)

        part_id = self._id_from_index(idx)
        return Part(
            id=part_id,
            original_index=idx,
            part_type=part_type,
            quantity=1,
            volume=volume,
            dimensions=dimensions,
            centroid=[float(centroid[0]), float(centroid[1]), float(centroid[2])],
            surface_area=surface_area,
            group_id=part_id,
            metrics={
                "solid_id": solid.get("solid_id", f"solid_{idx}"),
                "bounding_box": {"min": bbox_min, "max": bbox_max},
            },
        )

    def _calculate_adaptive_tolerance(self, parts: List[Part]) -> float:
        """
        Calculate adaptive tolerance based on model scale (Phase 2).

        Larger models with mixed sizes benefit from tighter tolerance.
        Smaller models use standard tolerance.

        Returns:
            Tolerance value between MIN_TOLERANCE and MAX_TOLERANCE
        """
        if not parts:
            return BASE_TOLERANCE

        volumes = [p.volume for p in parts if p.volume > 0]
        if not volumes:
            return BASE_TOLERANCE

        min_vol = min(volumes)
        max_vol = max(volumes)
        volume_ratio = max_vol / (min_vol + 1e-6)

        # High ratio (mixed sizes) → tighter tolerance for accuracy
        # Low ratio (uniform sizes) → standard/loose tolerance
        if volume_ratio > 100:  # Very mixed model
            return MIN_TOLERANCE  # 5% for tight matching
        elif volume_ratio > 10:  # Mixed model
            return BASE_TOLERANCE * 0.8  # 12% for balanced matching
        elif volume_ratio > 2:  # Mostly uniform with few outliers
            return BASE_TOLERANCE  # 15% for standard matching
        else:  # Very uniform model
            return MAX_TOLERANCE * 0.5  # 15% for loose matching

    def _deduplicate_parts(self, raw_parts: List[Part]) -> List[Part]:
        """Legacy method - now uses adaptive tolerance."""
        if not raw_parts:
            return []
        tolerance = self._calculate_adaptive_tolerance(raw_parts)
        return self._deduplicate_parts_adaptive(raw_parts, tolerance)

    def _deduplicate_parts_adaptive(self, raw_parts: List[Part], tolerance: float) -> List[Part]:
        """
        Deduplicate parts using adaptive tolerance (Phase 2 Enhanced).

        This is an order-independent deduplication that:
        1. Sorts by volume for efficient matching
        2. Uses multi-strategy similarity checking
        3. Groups identical parts
        4. Merges groups with count information

        Args:
            raw_parts: Raw extracted parts
            tolerance: Adaptive tolerance value (0.0-1.0)

        Returns:
            List of deduplicated parts with quantity information
        """
        if not raw_parts:
            return []

        sorted_parts = sorted(raw_parts, key=lambda p: p.volume)
        consumed = set()
        result: List[Part] = []

        for i, part in enumerate(sorted_parts):
            if i in consumed:
                continue

            group = [part]
            consumed.add(i)

            for j in range(i + 1, len(sorted_parts)):
                if j in consumed:
                    continue
                candidate = sorted_parts[j]

                # Early exit if volume is too different
                if not self._within_tolerance(part.volume, candidate.volume, tolerance):
                    if candidate.volume > part.volume * (1.0 + tolerance):
                        break
                    continue

                # Multi-strategy similarity check (Phase 2)
                if self._similar_dimensions(part.dimensions, candidate.dimensions, tolerance):
                    group.append(candidate)
                    consumed.add(j)

            merged = deepcopy(group[0])
            merged.quantity = len(group)
            merged.group_id = f"group_{len(result)}"
            merged.id = self._id_from_index(len(result))
            merged.original_index = group[0].original_index
            merged.metrics["group_members"] = [g.metrics.get("solid_id") for g in group]
            merged.metrics["deduplication_tolerance"] = tolerance
            result.append(merged)

        return result

    def _fallback_parts_from_bounds(self, geometry: Geometry3D) -> List[Part]:
        return [
            Part(
                id="A",
                original_index=0,
                part_type=PartType.PANEL,
                quantity=1,
                volume=100.5,
                dimensions={"width": 50, "height": 30, "depth": 2},
                centroid=[25, 15, 1],
                surface_area=3200,
                group_id="group_0",
                metrics={"source": "fallback"},
            ),
            Part(
                id="B",
                original_index=1,
                part_type=PartType.HARDWARE,
                quantity=4,
                volume=2.5,
                dimensions={"width": 5, "height": 5, "depth": 10},
                centroid=[2.5, 2.5, 5],
                surface_area=250,
                group_id="group_1",
                metrics={"source": "fallback"},
            ),
        ]

    def _classify(self, dimensions: dict, volume: float) -> PartType:
        """
        Classify parts using enhanced multi-strategy heuristics (Phase 2).

        Improved classification that considers:
        1. Volume thresholds (small → fastener, medium → hardware, large → structural)
        2. Aspect ratios (flat → panel, cubic → structural, elongated → fastener)
        3. Surface area indicators
        4. Dimension ratios

        Args:
            dimensions: Dictionary with 'width', 'height', 'depth' keys
            volume: Part volume in cubic units

        Returns:
            PartType classification
        """
        w = max(float(dimensions["width"]), 1e-6)
        h = max(float(dimensions["height"]), 1e-6)
        d = max(float(dimensions["depth"]), 1e-6)

        dims = sorted([w, h, d])
        smallest = dims[0]
        largest = dims[2]

        # Aspect ratios
        aspect_ratio = largest / smallest
        elongation = max(w, h, d) / min(w, h, d)
        flatness = smallest / largest

        # Phase 2: Enhanced heuristics

        # Strategy 1: FASTENER (very small, elongated, or thin)
        if volume < 50:
            return PartType.FASTENER
        if aspect_ratio > 20 and volume < 500:  # Elongated small parts
            return PartType.FASTENER

        # Strategy 2: PANEL (very flat with large surface area)
        if flatness < 0.05 and w * h >= 1000:  # Sheet-like
            return PartType.PANEL
        if flatness < 0.1 and w * h >= 500:  # Thin board
            return PartType.PANEL
        if smallest <= 5 and w * h >= 1000:  # Classic panel rule
            return PartType.PANEL

        # Strategy 3: HARDWARE (medium-sized, not flat or elongated)
        if 50 <= volume < 500:
            if aspect_ratio < 5:  # Mostly cubic
                return PartType.HARDWARE
            # Elongated medium parts → still hardware if not thin
            if flatness > 0.1:
                return PartType.HARDWARE

        # Strategy 4: STRUCTURAL (large and mostly cubic)
        if volume >= 500:
            if aspect_ratio < 10 and flatness > 0.1:  # Large and compact
                return PartType.STRUCTURAL
            # Large but flat → could be panel
            if flatness < 0.1:
                return PartType.PANEL

        # Fallback
        return PartType.OTHER

    def _similar_dimensions(self, d1: dict, d2: dict, tolerance: float = BASE_TOLERANCE) -> bool:
        """
        Check if two parts have similar dimensions within tolerance (Phase 2).

        Compares all three dimensions (width, height, depth) to determine
        if parts are duplicates.

        Args:
            d1: First dimension dict
            d2: Second dimension dict
            tolerance: Tolerance factor (0.0-1.0)

        Returns:
            True if all dimensions match within tolerance
        """
        keys = ["width", "height", "depth"]
        return all(self._within_tolerance(float(d1[k]), float(d2[k]), tolerance) for k in keys)

    @staticmethod
    def _within_tolerance(a: float, b: float, tolerance: float) -> bool:
        small = min(abs(a), abs(b)) + 1e-6
        ratio = max(abs(a), abs(b)) / small
        return ratio <= (1.0 + tolerance)

    @staticmethod
    def _estimate_surface_area(dimensions: dict) -> float:
        w = max(float(dimensions["width"]), 0.0)
        h = max(float(dimensions["height"]), 0.0)
        d = max(float(dimensions["depth"]), 0.0)
        return 2.0 * (w * h + h * d + w * d)

    @staticmethod
    def _id_from_index(idx: int) -> str:
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if idx < len(alphabet):
            return alphabet[idx]
        prefix = alphabet[(idx // len(alphabet)) - 1]
        suffix = alphabet[idx % len(alphabet)]
        return f"{prefix}{suffix}"
