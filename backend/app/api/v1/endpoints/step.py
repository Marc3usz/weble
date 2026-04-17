import uuid
import logging
import json
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from fastapi.responses import StreamingResponse

from app.container import get_container, ServiceContainer
from app.core.config import settings
from app.core.exceptions import InvalidStepFileError
from app.models.schemas import (
    AssemblyResponse,
    AssemblyStepSchema,
    PartSchema,
    PartsResponse,
    ProcessingStatus,
    ProgressStreamResponse,
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
    Client can subscribe to SSE to track progress via GET /api/v1/step/progress/{job_id}/stream

    Args:
        file: STEP/STP file to upload (max 50 MB)
        background_tasks: FastAPI background tasks for async processing
        container: Service container with repository and progress tracker

    Returns:
        UploadResponse with job_id, model_id, and initial status

    Raises:
        InvalidStepFileError: If file is invalid or exceeds size limit
        ValueError: If database not initialized
    """

    file_content = await file.read()

    # Validate file size
    file_size = len(file_content)
    max_file_size_bytes = settings.max_file_size_mb * 1024 * 1024
    if file_size > max_file_size_bytes:
        raise InvalidStepFileError(
            f"File size {file_size} exceeds max size {max_file_size_bytes} bytes"
        )

    # Validate STEP file format
    if not await StepLoaderService().validate_input(file_content):
        raise InvalidStepFileError("File is not a valid STEP file or too small")

    # Generate unique IDs
    model_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())

    # Get repository from container
    repository = await container.get_repository()

    # Create model and job records
    await repository.create_model(model_id, file.filename or "unknown", file_size)
    await repository.create_job(job_id, model_id, ProcessingStatus.PROCESSING)

    logger.info(f"Created upload job {job_id} for model {model_id}, file size: {file_size} bytes")

    # Start background pipeline
    if background_tasks:
        pipeline = ProcessingPipeline(container)
        background_tasks.add_task(
            pipeline.process_step_file,
            model_id,
            file_content,
            job_id,
        )

    return UploadResponse(
        job_id=job_id,
        model_id=model_id,
        status="processing",
        estimated_time_seconds=60,
    )


@router.get("/step/{model_id}")
async def get_step_model(
    model_id: str, container: ServiceContainer = Depends(get_container)
) -> dict:
    """Get processed STEP model data.

    Args:
        model_id: UUID of the model to retrieve
        container: Service container with repository

    Returns:
        Dictionary with model metadata and geometry status
    """
    repository = await container.get_repository()

    model = await repository.get_model(model_id)
    if model is None:
        return {"error": "Model not found"}

    geometry = await repository.get_geometry(model_id)

    return {
        "status": "success",
        "model_id": model_id,
        "file_name": model.get("file_name"),
        "file_size": model.get("file_size"),
        "geometry_loaded": geometry is not None,
    }


@router.post("/step/parts-2d", response_model=PartsResponse)
async def generate_parts_2d(
    payload: dict,
    container: ServiceContainer = Depends(get_container),
) -> PartsResponse:
    """Generate or return extracted parts with 2D drawing metadata.

    Args:
        payload: Request body with model_id
        container: Service container with repository

    Returns:
        PartsResponse with extracted parts and metadata

    Raises:
        ValueError: If model_id missing, model not found, or geometry unavailable
    """
    model_id = payload.get("modelId") or payload.get("model_id")
    if not model_id:
        raise ValueError("modelId is required")

    repository = await container.get_repository()

    model = await repository.get_model(model_id)
    if model is None:
        raise ValueError("Model not found")

    parts = await repository.get_parts(model_id)
    if not parts:
        geometry = await repository.get_geometry(model_id)
        if geometry is None:
            raise ValueError("Model geometry is not available")

        extractor = PartsExtractorService()
        parts = await extractor.process(geometry)
        await repository.save_parts(model_id, parts)

        svg_generator = SvgGeneratorService()
        drawings = await svg_generator.process(parts)
        await repository.save_drawings(model_id, drawings)

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
    """Generate or return assembly analysis for a model.

    Args:
        payload: Request body with model_id
        preview_only: If True, skip AI generation for faster preview
        container: Service container with repository

    Returns:
        AssemblyResponse with assembly steps and metadata

    Raises:
        ValueError: If model_id missing, model not found, or geometry unavailable
    """
    model_id = payload.get("modelId") or payload.get("model_id")
    if not model_id:
        raise ValueError("modelId is required")

    repository = await container.get_repository()

    model = await repository.get_model(model_id)
    if model is None:
        raise ValueError("Model not found")

    parts = await repository.get_parts(model_id)
    drawings = await repository.get_drawings(model_id)

    if not parts:
        geometry = await repository.get_geometry(model_id)
        if geometry is None:
            raise ValueError("Model geometry is not available")
        parts = await PartsExtractorService().process(geometry)
        await repository.save_parts(model_id, parts)

    if not drawings:
        drawings = await SvgGeneratorService().process(parts)
        await repository.save_drawings(model_id, drawings)

    steps = await AssemblyGeneratorService().process(parts, drawings, preview_only=preview_only)
    await repository.save_steps(model_id, steps)

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


@router.get("/step/progress/{job_id}/stream")
async def stream_progress(
    job_id: str,
    container: ServiceContainer = Depends(get_container),
) -> StreamingResponse:
    """
    Stream job progress via Server-Sent Events (SSE).

    Client can subscribe to this endpoint to receive real-time progress updates
    while the STEP file is being processed.

    Args:
        job_id: UUID of the processing job
        container: Service container with progress tracker

    Returns:
        StreamingResponse with SSE events

    Example usage (JavaScript):
        const eventSource = new EventSource(`/api/v1/step/progress/${jobId}/stream`);
        eventSource.onmessage = (event) => {
            const progress = JSON.parse(event.data);
            console.log(`Progress: ${progress.progress_percent}% - ${progress.action}`);
        };
        eventSource.onerror = () => eventSource.close();
    """
    progress_tracker = await container.get_progress_tracker()
    queue = await progress_tracker.subscribe(job_id)

    async def event_generator():
        """Generate SSE events from progress queue."""
        try:
            while True:
                # Get next progress event
                try:
                    progress_event = queue.get_nowait()
                except Exception:
                    # Queue empty, wait a bit
                    import asyncio

                    await asyncio.sleep(0.1)
                    continue

                # Convert to response format
                response = ProgressStreamResponse(
                    job_id=job_id,
                    status=progress_event.status,
                    progress_percent=progress_event.percentage,
                    current_stage=progress_event.stage,
                    action=progress_event.message,
                    eta_seconds=progress_event.data.get("eta_seconds", 0),
                    error_message=progress_event.data.get("error_message"),
                    timestamp=progress_event.data.get("timestamp"),
                )

                # Format as SSE
                yield f"data: {response.model_dump_json()}\n\n"

                # Break if job is complete or failed
                if progress_event.status in ["complete", "failed"]:
                    break

        finally:
            await progress_tracker.unsubscribe(job_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        },
    )


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    container: ServiceContainer = Depends(get_container),
) -> dict:
    """Get the current status of a processing job.

    Args:
        job_id: UUID of the processing job
        container: Service container with repository

    Returns:
        Job status with progress information
    """
    repository = await container.get_repository()
    job = await repository.get_job(job_id)

    if job is None:
        return {"error": "Job not found"}

    return {
        "job_id": job.id,
        "model_id": job.model_id,
        "status": job.status.value,
        "progress_percent": job.progress_percent,
        "current_stage": job.current_stage,
        "action": job.action,
        "eta_seconds": job.eta_seconds,
        "error_message": job.error_message,
    }
