"""Pipeline orchestration - coordinates all 4 stages."""

import logging
from app.container import ServiceContainer
from app.models.schemas import ProcessingStatus
from app.services.progress_tracker import ProgressEvent
from app.services.step_loader import StepLoaderService
from app.services.parts_extractor import PartsExtractorService
from app.services.svg_generator import SvgGeneratorService
from app.services.assembly_generator import AssemblyGeneratorService

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """
    Orchestrates the full 4-stage processing pipeline:

    Stage 1: STEP Loading (file → geometry)
    Stage 2: Parts Extraction (geometry → parts)
    Stage 3: SVG Generation (parts → drawings)
    Stage 4: Assembly Generation (parts + drawings → steps)
    """

    def __init__(self, container: ServiceContainer) -> None:
        self.container = container
        self.logger = logging.getLogger(__name__)

        # Initialize services
        self.step_loader = StepLoaderService()
        self.parts_extractor = PartsExtractorService()
        self.svg_generator = SvgGeneratorService()
        self.assembly_generator = AssemblyGeneratorService()

    async def process_step_file(self, model_id: str, file_content: bytes, job_id: str) -> None:
        """
        Run the full pipeline as a background task.

        Updates job status and emits progress via SSE at each stage.
        """
        db = self.container._db
        tracker = self.container._progress_tracker

        if db is None or tracker is None:
            self.logger.error("Database or tracker not initialized")
            return

        try:
            # ========== STAGE 1: Load STEP File ==========
            self.logger.info(f"[{job_id}] Starting Stage 1: STEP Loading")
            await db.update_job(job_id, ProcessingStatus.PROCESSING, 0, "loading")
            await tracker.emit(
                job_id,
                ProgressEvent(
                    stage="1", status="loading", percentage=5, message="Loading STEP file..."
                ),
            )

            geometry = await self.step_loader.process(file_content)
            await db.save_geometry(model_id, geometry)

            await tracker.emit(
                job_id,
                ProgressEvent(
                    stage="1",
                    status="complete",
                    percentage=25,
                    message="Stage 1 complete: Geometry loaded",
                ),
            )
            self.logger.info(f"[{job_id}] Stage 1 complete")

            # ========== STAGE 2: Extract Parts ==========
            self.logger.info(f"[{job_id}] Starting Stage 2: Parts Extraction")
            await db.update_job(job_id, ProcessingStatus.PROCESSING, 25, "extracting")
            await tracker.emit(
                job_id,
                ProgressEvent(
                    stage="2",
                    status="extracting",
                    percentage=30,
                    message="Extracting and classifying parts...",
                ),
            )

            parts = await self.parts_extractor.process(geometry)
            await db.save_parts(model_id, parts)

            await tracker.emit(
                job_id,
                ProgressEvent(
                    stage="2",
                    status="complete",
                    percentage=50,
                    message=f"Stage 2 complete: {len(parts)} parts extracted",
                ),
            )
            self.logger.info(f"[{job_id}] Stage 2 complete: {len(parts)} parts")

            # ========== STAGE 3: Generate SVG Drawings ==========
            self.logger.info(f"[{job_id}] Starting Stage 3: SVG Generation")
            await db.update_job(job_id, ProcessingStatus.PROCESSING, 50, "drawing")
            await tracker.emit(
                job_id,
                ProgressEvent(
                    stage="3",
                    status="generating",
                    percentage=60,
                    message="Generating technical drawings...",
                ),
            )

            drawings = await self.svg_generator.process(parts)
            await db.save_drawings(model_id, drawings)

            await tracker.emit(
                job_id,
                ProgressEvent(
                    stage="3",
                    status="complete",
                    percentage=75,
                    message=f"Stage 3 complete: {len(drawings)} drawings generated",
                ),
            )
            self.logger.info(f"[{job_id}] Stage 3 complete")

            # ========== STAGE 4: Generate Assembly Instructions ==========
            self.logger.info(f"[{job_id}] Starting Stage 4: Assembly Generation")
            await db.update_job(job_id, ProcessingStatus.PROCESSING, 75, "assembly")
            await tracker.emit(
                job_id,
                ProgressEvent(
                    stage="4",
                    status="generating",
                    percentage=80,
                    message="Generating assembly instructions...",
                ),
            )

            steps = await self.assembly_generator.process(parts, drawings, preview_only=False)
            await db.save_steps(model_id, steps)

            await tracker.emit(
                job_id,
                ProgressEvent(
                    stage="4",
                    status="complete",
                    percentage=100,
                    message=f"Stage 4 complete: {len(steps)} assembly steps",
                ),
            )
            self.logger.info(f"[{job_id}] Stage 4 complete")

            # ========== COMPLETION ==========
            await db.update_job(job_id, ProcessingStatus.COMPLETE, 100, "complete")
            await tracker.emit(
                job_id,
                ProgressEvent(
                    stage="complete",
                    status="success",
                    percentage=100,
                    message="Pipeline completed successfully",
                ),
            )

            self.logger.info(f"[{job_id}] Pipeline completed successfully")

        except Exception as e:
            self.logger.exception(f"[{job_id}] Pipeline failed: {e}")
            await db.update_job(job_id, ProcessingStatus.FAILED, error_message=str(e))
            await tracker.emit(
                job_id,
                ProgressEvent(
                    stage="error", status="failed", percentage=0, message=f"Error: {str(e)}"
                ),
            )
