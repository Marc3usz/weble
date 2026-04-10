"""Job status endpoints."""

import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.container import get_container, ServiceContainer
from app.models.schemas import JobStatusResponse

router = APIRouter()


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str, container: ServiceContainer = Depends(get_container)
) -> JobStatusResponse:
    """Get the status of a processing job."""
    db = container._db
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")

    job = await db.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.id,
        status=job.status.value,
        progress_percent=job.progress_percent,
        current_stage=job.current_stage,
        error_message=job.error_message,
    )


@router.get("/jobs/{job_id}/sse")
async def stream_job_progress(
    job_id: str, container: ServiceContainer = Depends(get_container)
) -> StreamingResponse:
    """
    Stream job progress via Server-Sent Events.

    Client subscribes and receives real-time progress updates.
    """
    tracker = container._progress_tracker
    if tracker is None:
        raise HTTPException(status_code=500, detail="Progress tracker not initialized")

    queue = await tracker.subscribe(job_id)

    async def event_generator():
        try:
            while True:
                try:
                    # Wait for next event with timeout
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(event.to_dict())}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield f": heartbeat\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            await tracker.unsubscribe(job_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
