import uuid
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile

from app.container import get_container, ServiceContainer
from app.core.config import settings
from app.core.exceptions import InvalidStepFileError
from app.models.schemas import (
    AssemblyResponse,
    AssemblyStepSchema,
    PartSchema,
    PartsResponse,
    ProcessingStatus,
    UploadResponse,
)
from app.services.assembly_generator import AssemblyGeneratorService
from app.services.parts_extractor import PartsExtractorService
from app.services.step_loader import StepLoaderService
from app.services.svg_generator import SvgGeneratorService
from app.workers.pipeline import ProcessingPipeline

"""STEP file processing endpoints."""

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/step/upload", response_model=UploadResponse)
async def upload_step_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    container: ServiceContainer = Depends(get_container),
) -> UploadResponse:
    """
    Upload and process a STEP file.

    Returns immediately with job ID, processes in background.
    Client can subscribe to SSE to track progress.
    """

    file_content = await file.read()

    file_size = len(file_content)
    max_file_size_bytes = settings.max_file_size_mb * 1024 * 1024
    if file_size > max_file_size_bytes:
        raise InvalidStepFileError(
            f"File size {file_size} exceeds max size {max_file_size_bytes} bytes"
        )

    # Validate upfront so invalid files return immediate error status.
    if not await StepLoaderService().validate_input(file_content):
        raise InvalidStepFileError("File is not a valid STEP file or too small")

    # Generate IDs
    model_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())

    # Create job record
    db = container._db
    if db is None:
        raise ValueError("Database not initialized")

    await db.create_model(model_id, file.filename or "unknown", file_size)
    await db.create_job(job_id, model_id, ProcessingStatus.PROCESSING)

    # Start background pipeline
    if background_tasks:
        pipeline = ProcessingPipeline(container)
        background_tasks.add_task(pipeline.process_step_file, model_id, file_content, job_id)

    logger.info(f"Created upload job {job_id} for model {model_id}")

    return UploadResponse(
        job_id=job_id, model_id=model_id, status="processing", estimated_time_seconds=60
    )


@router.get("/step/{model_id}")
async def get_step_model(
    model_id: str, container: ServiceContainer = Depends(get_container)
) -> dict:
    """Get processed STEP model data."""
    db = container._db
    if db is None:
        raise ValueError("Database not initialized")

    model = await db.get_model(model_id)
    if model is None:
        return {"error": "Model not found"}

    return {
        "status": "success",
        "model_id": model_id,
        "file_name": model.get("file_name"),
        "file_size": model.get("file_size"),
        "geometry_loaded": model.get("geometry") is not None,
    }


@router.post("/step/parts-2d", response_model=PartsResponse)
async def generate_parts_2d(
    payload: dict,
    container: ServiceContainer = Depends(get_container),
) -> PartsResponse:
    """Generate or return extracted parts with 2D drawing metadata."""
    model_id = payload.get("modelId") or payload.get("model_id")
    if not model_id:
        raise ValueError("modelId is required")

    db = container._db
    if db is None:
        raise ValueError("Database not initialized")

    model = await db.get_model(model_id)
    if model is None:
        raise ValueError("Model not found")

    parts = await db.get_parts(model_id)
    if not parts:
        geometry = model.get("geometry")
        if geometry is None:
            raise ValueError("Model geometry is not available")

        extractor = PartsExtractorService()
        parts = await extractor.process(geometry)
        await db.save_parts(model_id, parts)

        svg_generator = SvgGeneratorService()
        drawings = await svg_generator.process(parts)
        await db.save_drawings(model_id, drawings)

    return PartsResponse(
        model_id=model_id,
        parts=[
            PartSchema(
                id=part.id,
                part_type=part.part_type.value,
                quantity=part.quantity,
                volume=part.volume,
                dimensions=part.dimensions,
            )
            for part in parts
        ],
        total_parts=len(parts),
    )


@router.post("/step/assembly-analysis", response_model=AssemblyResponse)
async def generate_assembly_analysis(
    payload: dict,
    preview_only: bool = False,
    container: ServiceContainer = Depends(get_container),
) -> AssemblyResponse:
    """Generate or return assembly analysis for a model."""
    model_id = payload.get("modelId") or payload.get("model_id")
    if not model_id:
        raise ValueError("modelId is required")

    db = container._db
    if db is None:
        raise ValueError("Database not initialized")

    model = await db.get_model(model_id)
    if model is None:
        raise ValueError("Model not found")

    parts = await db.get_parts(model_id)
    drawings = await db.get_drawings(model_id)

    if not parts:
        geometry = model.get("geometry")
        if geometry is None:
            raise ValueError("Model geometry is not available")
        parts = await PartsExtractorService().process(geometry)
        await db.save_parts(model_id, parts)

    if not drawings:
        drawings = await SvgGeneratorService().process(parts)
        await db.save_drawings(model_id, drawings)

    steps = await AssemblyGeneratorService().process(parts, drawings, preview_only=preview_only)
    await db.save_steps(model_id, steps)

    return AssemblyResponse(
        model_id=model_id,
        steps=[
            AssemblyStepSchema(
                step_number=step.step_number,
                title=step.title,
                description=step.description,
                part_indices=step.part_indices,
                part_roles=step.part_roles,
                context_part_indices=step.context_part_indices,
                duration_minutes=step.duration_minutes,
            )
            for step in steps
        ],
        total_steps=len(steps),
    )
