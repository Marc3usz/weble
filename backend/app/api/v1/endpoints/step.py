"""STEP file processing endpoints."""

import uuid
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends
import logging

from app.container import get_container, ServiceContainer
from app.models.schemas import UploadResponse, ProcessingStatus
from app.workers.pipeline import ProcessingPipeline

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

    # Generate IDs
    model_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())

    # Create job record
    db = container._db
    if db is None:
        raise ValueError("Database not initialized")

    file_content = await file.read()
    file_size = len(file_content)

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
