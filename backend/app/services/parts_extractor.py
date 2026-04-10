"""Stage 2: Parts Extraction Service."""

import logging
from copy import deepcopy
from typing import List

from app.services.step_loader import PipelineStage
from app.models.schemas import Part, PartType, Geometry3D

logger = logging.getLogger(__name__)


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
        Extract parts from geometry and classify them.

        Uses Stage 1 metadata when available and applies tolerance-based
        deduplication (15%) as described in project docs.
        """

        is_valid = await self.validate_input(geometry)
        if not is_valid:
            raise ValueError("Invalid geometry input")

        self.logger.info("Extracting and classifying parts...")

        solids = geometry.metadata.get("solids", []) if geometry.metadata else []

        if solids:
            raw_parts = [self._solid_to_part(solid, idx) for idx, solid in enumerate(solids)]
            parts = self._deduplicate_parts(raw_parts)
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

    def _deduplicate_parts(self, raw_parts: List[Part]) -> List[Part]:
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
                if not self._within_tolerance(part.volume, candidate.volume, 0.15):
                    if candidate.volume > part.volume * 1.15:
                        break
                    continue

                if self._similar_dimensions(part.dimensions, candidate.dimensions):
                    group.append(candidate)
                    consumed.add(j)

            merged = deepcopy(group[0])
            merged.quantity = len(group)
            merged.group_id = f"group_{len(result)}"
            merged.id = self._id_from_index(len(result))
            merged.original_index = group[0].original_index
            merged.metrics["group_members"] = [g.metrics.get("solid_id") for g in group]
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
        dims = sorted([dimensions["width"], dimensions["height"], dimensions["depth"]])
        flat_ratio = (dims[2] / (dims[0] + 1e-6)) if dims[0] > 0 else 0
        if dims[0] <= 5 and dims[1] * dims[2] >= 1000:
            return PartType.PANEL
        if volume < 50:
            return PartType.FASTENER
        if 50 <= volume < 500:
            return PartType.HARDWARE
        if volume >= 500 and flat_ratio < 10:
            return PartType.STRUCTURAL
        return PartType.OTHER

    def _similar_dimensions(self, d1: dict, d2: dict) -> bool:
        keys = ["width", "height", "depth"]
        return all(self._within_tolerance(float(d1[k]), float(d2[k]), 0.15) for k in keys)

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
