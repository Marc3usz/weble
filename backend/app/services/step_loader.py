"""Stage 1: STEP Loading Service."""

import asyncio
import hashlib
import logging
import math
import os
import re
import tempfile
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from app.models.schemas import Geometry3D
from app.core.exceptions import InvalidStepFileError

try:
    import cadquery as cq
except Exception:  # pragma: no cover - optional dependency path
    cq = None

logger = logging.getLogger(__name__)


class PipelineStage(ABC):
    """Base class for all pipeline stages."""

    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """Process input data and return output."""
        pass

    @abstractmethod
    async def validate_input(self, data: Any) -> bool:
        """Validate that input meets requirements."""
        pass


class StepLoaderService(PipelineStage):
    """
    Stage 1: Load STEP file and extract 3D geometry.

    Input:  STEP file content (bytes)
    Output: Geometry3D (vertices, normals, indices)
    """

    def __init__(self) -> None:
        self.name = "StepLoaderService"
        self.logger = logging.getLogger(__name__)

    async def validate_input(self, data: bytes) -> bool:
        """Validate that input is a valid STEP file."""
        if not isinstance(data, bytes):
            return False
        if len(data) < 100:  # Minimal STEP file size
            return False
        if not data.startswith(b"ISO-10303-21"):  # STEP file signature
            return False
        return True

    async def process(self, file_content: bytes) -> Geometry3D:
        """
        Load STEP file and extract geometry.

        Strategy:
        1) Prefer CadQuery if available.
        2) Fall back to STEP-text parsing for portable development mode.
        """

        is_valid = await self.validate_input(file_content)
        if not is_valid:
            raise InvalidStepFileError("File is not a valid STEP file or too small")

        self.logger.info("Loading STEP file...")

        try:
            if cq is not None:
                try:
                    # Run blocking CadQuery operation in thread pool
                    geometry = await asyncio.get_event_loop().run_in_executor(
                        None, self._load_with_cadquery, file_content
                    )
                    self.logger.info(
                        "Loaded geometry via CadQuery: %s vertices",
                        len(geometry.vertices),
                    )
                    return geometry
                except Exception as cad_error:
                    self.logger.warning("CadQuery loader failed, falling back: %s", cad_error)

            # Run blocking fallback operation in thread pool
            geometry = await asyncio.get_event_loop().run_in_executor(
                None, self._load_with_step_text_fallback, file_content
            )
            self.logger.info(
                "Loaded geometry via fallback parser: %s vertices",
                len(geometry.vertices),
            )
            return geometry

        except Exception as e:
            self.logger.error(f"Failed to load STEP file: {e}")
            raise InvalidStepFileError(f"Failed to parse STEP file: {str(e)}")

    def _load_with_cadquery(self, file_content: bytes) -> Geometry3D:
        """Load STEP using CadQuery and triangulate each solid."""
        temp_path = ""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".step") as tmp:
                tmp.write(file_content)
                temp_path = tmp.name

            model = cq.importers.importStep(temp_path)
            solids = list(model.solids().vals())
            if not solids:
                raise InvalidStepFileError("No solids found in STEP file")

            vertices: List[List[float]] = []
            normals: List[List[float]] = []
            indices: List[int] = []
            solids_metadata: List[Dict[str, Any]] = []
            vertex_offset = 0

            for idx, solid in enumerate(solids):
                bbox = solid.BoundingBox()
                v_min = [float(bbox.xmin), float(bbox.ymin), float(bbox.zmin)]
                v_max = [float(bbox.xmax), float(bbox.ymax), float(bbox.zmax)]

                solid_vertices, solid_indices = self._tessellate_solid(solid)
                if not solid_vertices or not solid_indices:
                    # Fallback to an AABB mesh only if tessellation failed for this solid.
                    solid_vertices, solid_indices = self._build_box_mesh(v_min, v_max)

                solid_normals = self._compute_vertex_normals(solid_vertices)

                solid_vertex_start = vertex_offset
                solid_vertex_count = len(solid_vertices)
                solid_index_start = len(indices)
                solid_index_count = len(solid_indices)

                vertices.extend(solid_vertices)
                normals.extend(solid_normals)
                indices.extend([i + vertex_offset for i in solid_indices])
                vertex_offset += len(solid_vertices)

                center = solid.Center()
                solids_metadata.append(
                    {
                        "solid_id": f"solid_{idx}",
                        "volume": float(solid.Volume()),
                        "centroid": [float(center.x), float(center.y), float(center.z)],
                        "bounding_box": {"min": v_min, "max": v_max},
                        "vertex_start": solid_vertex_start,
                        "vertex_count": solid_vertex_count,
                        "index_start": solid_index_start,
                        "index_count": solid_index_count,
                    }
                )

            bounds = self._bounds_from_vertices(vertices)
            return Geometry3D(
                vertices=vertices,
                normals=normals,
                indices=indices,
                metadata={
                    "solids_count": len(solids),
                    "solids": solids_metadata,
                    "bounds": bounds,
                    "total_triangles": len(indices) // 3,
                    "source": "cadquery",
                    "file_hash": hashlib.sha256(file_content).hexdigest(),
                },
            )
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    def _tessellate_solid(self, solid: Any, tolerance: float = 0.15) -> Tuple[List[List[float]], List[int]]:
        """
        Tessellate a CadQuery solid into triangle mesh.

        Returns:
            (vertices, indices) where vertices are [[x, y, z], ...] and
            indices are flat triangle indices [i0, i1, i2, ...].
        """
        try:
            # CadQuery Shape.tessellate returns (vertices, triangles)
            # vertices: list[Vector], triangles: list[tuple[int, int, int]]
            tess_vertices, tess_triangles = solid.tessellate(tolerance)
        except TypeError:
            # Some CadQuery versions expose angular tolerance as second arg
            tess_vertices, tess_triangles = solid.tessellate(tolerance, 0.2)

        vertices: List[List[float]] = []
        for v in tess_vertices:
            vertices.append([float(v.x), float(v.y), float(v.z)])

        indices: List[int] = []
        for tri in tess_triangles:
            if len(tri) != 3:
                continue
            indices.extend([int(tri[0]), int(tri[1]), int(tri[2])])

        return vertices, indices

    def _load_with_step_text_fallback(self, file_content: bytes) -> Geometry3D:
        """Parse STEP ASCII points and generate a usable mesh."""
        text = file_content.decode("utf-8", errors="ignore")
        points = self._extract_cartesian_points(text)

        if len(points) < 3:
            raise InvalidStepFileError("Could not extract enough geometry points from STEP content")

        bounds = self._bounds_from_vertices(points)
        vertices, indices = self._mesh_from_points(points)
        normals = self._compute_vertex_normals(vertices)

        x_span = bounds["max"][0] - bounds["min"][0]
        y_span = bounds["max"][1] - bounds["min"][1]
        z_span = bounds["max"][2] - bounds["min"][2]
        estimated_volume = max(x_span, 1e-6) * max(y_span, 1e-6) * max(z_span, 1e-6)

        return Geometry3D(
            vertices=vertices,
            normals=normals,
            indices=indices,
            metadata={
                "solids_count": 1,
                "solids": [
                    {
                        "solid_id": "solid_0",
                        "volume": float(estimated_volume),
                        "centroid": [
                            (bounds["min"][0] + bounds["max"][0]) / 2.0,
                            (bounds["min"][1] + bounds["max"][1]) / 2.0,
                            (bounds["min"][2] + bounds["max"][2]) / 2.0,
                        ],
                        "bounding_box": bounds,
                    }
                ],
                "bounds": bounds,
                "total_triangles": len(indices) // 3,
                "source": "step-text-fallback",
                "file_hash": hashlib.sha256(file_content).hexdigest(),
            },
        )

    def _extract_cartesian_points(self, text: str) -> List[List[float]]:
        pattern = re.compile(r"CARTESIAN_POINT\s*\([^\(]*\(([^\)]*)\)\)", re.IGNORECASE)
        points: List[List[float]] = []
        for match in pattern.findall(text):
            chunks = [c.strip() for c in match.split(",")]
            if len(chunks) < 3:
                continue
            try:
                points.append([float(chunks[0]), float(chunks[1]), float(chunks[2])])
            except ValueError:
                continue

        # If CAD points are sparse or absent, infer an axis-aligned box from all numbers.
        if len(points) >= 3:
            return points

        numbers = []
        for token in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text):
            try:
                numbers.append(float(token))
            except ValueError:
                pass

        if len(numbers) < 6:
            return []

        sample = numbers[: min(300, len(numbers))]
        mn = min(sample)
        mx = max(sample)
        if math.isclose(mn, mx):
            mx = mn + 1.0
        return self._build_box_vertices([mn, mn, mn], [mx, mx, mx])

    def _mesh_from_points(self, points: List[List[float]]) -> Tuple[List[List[float]], List[int]]:
        unique: List[List[float]] = []
        seen = set()
        for p in points:
            key = (round(p[0], 6), round(p[1], 6), round(p[2], 6))
            if key in seen:
                continue
            seen.add(key)
            unique.append([float(p[0]), float(p[1]), float(p[2])])

        if len(unique) >= 8:
            bounds = self._bounds_from_vertices(unique)
            vertices, indices = self._build_box_mesh(bounds["min"], bounds["max"])
            return vertices, indices

        if len(unique) == 3:
            return unique, [0, 1, 2]

        indices: List[int] = []
        for i in range(1, len(unique) - 1):
            indices.extend([0, i, i + 1])
        return unique, indices

    def _build_box_vertices(self, v_min: List[float], v_max: List[float]) -> List[List[float]]:
        return [
            [v_min[0], v_min[1], v_min[2]],
            [v_max[0], v_min[1], v_min[2]],
            [v_max[0], v_max[1], v_min[2]],
            [v_min[0], v_max[1], v_min[2]],
            [v_min[0], v_min[1], v_max[2]],
            [v_max[0], v_min[1], v_max[2]],
            [v_max[0], v_max[1], v_max[2]],
            [v_min[0], v_max[1], v_max[2]],
        ]

    def _build_box_mesh(
        self, v_min: List[float], v_max: List[float]
    ) -> Tuple[List[List[float]], List[int]]:
        vertices = self._build_box_vertices(v_min, v_max)
        indices = [
            0,
            1,
            2,
            0,
            2,
            3,
            4,
            6,
            5,
            4,
            7,
            6,
            0,
            4,
            5,
            0,
            5,
            1,
            1,
            5,
            6,
            1,
            6,
            2,
            2,
            6,
            7,
            2,
            7,
            3,
            3,
            7,
            4,
            3,
            4,
            0,
        ]
        return vertices, indices

    def _compute_vertex_normals(self, vertices: List[List[float]]) -> List[List[float]]:
        center = [
            sum(v[0] for v in vertices) / len(vertices),
            sum(v[1] for v in vertices) / len(vertices),
            sum(v[2] for v in vertices) / len(vertices),
        ]
        normals: List[List[float]] = []
        for v in vertices:
            dx = v[0] - center[0]
            dy = v[1] - center[1]
            dz = v[2] - center[2]
            mag = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
            normals.append([dx / mag, dy / mag, dz / mag])
        return normals

    def _bounds_from_vertices(self, vertices: List[List[float]]) -> Dict[str, List[float]]:
        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        zs = [v[2] for v in vertices]
        return {
            "min": [float(min(xs)), float(min(ys)), float(min(zs))],
            "max": [float(max(xs)), float(max(ys)), float(max(zs))],
        }
