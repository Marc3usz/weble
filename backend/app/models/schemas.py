"""Data models and Pydantic schemas."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel


class PartType(str, Enum):
    """Classification of parts."""

    PANEL = "panel"
    HARDWARE = "hardware"
    FASTENER = "fastener"
    STRUCTURAL = "structural"
    OTHER = "other"


class ProcessingStatus(str, Enum):
    """Status of a processing job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


# ============================================================================
# DATA MODELS (Internal, for service layer)
# ============================================================================


@dataclass
class Geometry3D:
    """Output of Stage 1: STEP Loading."""

    vertices: List[List[float]]  # [[x1, y1, z1], ...]
    normals: List[List[float]]  # [[nx1, ny1, nz1], ...]
    indices: List[int]  # Triangle indices
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Part:
    """Output of Stage 2: Parts Extraction."""

    id: str  # "A", "B", "C"
    original_index: int
    part_type: PartType
    quantity: int
    volume: float  # cm³
    dimensions: Dict[str, float]  # {width, height, depth}
    centroid: List[float]  # [x, y, z]
    surface_area: float
    group_id: str  # For deduplication
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SvgDrawing:
    """Output of Stage 3: SVG Generation."""

    part_id: str
    svg_content: str
    quantity_label: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AssemblyStep:
    """Output of Stage 4: Assembly Generation."""

    step_number: int
    title: str
    description: str
    part_indices: List[int]
    part_roles: Dict[int, str]
    context_part_indices: List[int] = field(default_factory=list)
    svg_diagram: str = ""
    duration_minutes: int = 0


@dataclass
class ProcessingJob:
    """Tracks processing pipeline progress."""

    id: str = field(default_factory=lambda: str(uuid4()))
    model_id: str = ""
    status: ProcessingStatus = ProcessingStatus.PENDING
    progress_percent: int = 0
    current_stage: str = ""
    error_message: Optional[str] = None


# ============================================================================
# PYDANTIC SCHEMAS (For API request/response)
# ============================================================================


class UploadResponse(BaseModel):
    """Response from POST /api/v1/step/upload."""

    job_id: str
    model_id: str
    status: str
    estimated_time_seconds: int


class JobStatusResponse(BaseModel):
    """Response from GET /api/v1/jobs/{job_id}."""

    job_id: str
    status: str
    progress_percent: int
    current_stage: str
    error_message: Optional[str] = None


class PartSchema(BaseModel):
    """Part schema for API responses."""

    id: str
    part_type: str
    quantity: int
    volume: float
    dimensions: Dict[str, float]


class PartsResponse(BaseModel):
    """Response from POST /api/v1/step/parts-2d."""

    model_id: str
    parts: List[PartSchema]
    total_parts: int


class AssemblyStepSchema(BaseModel):
    """Assembly step schema for API responses."""

    step_number: int
    title: str
    description: str
    part_indices: List[int]
    part_roles: Dict[int, str]
    context_part_indices: List[int]
    duration_minutes: int


class AssemblyResponse(BaseModel):
    """Response from POST /api/v1/step/assembly-analysis."""

    model_id: str
    steps: List[AssemblyStepSchema]
    total_steps: int


class HealthResponse(BaseModel):
    """Response from GET /api/v1/health."""

    status: str
    version: str = "0.1.0"
    message: str = "API is healthy"
