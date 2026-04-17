"""Pipeline orchestration - coordinates all 4 stages."""

import logging
import asyncio
from app.container import ServiceContainer
from app.models.schemas import ProcessingStatus
from app.services.progress_tracker import ProgressEvent
from app.services.step_loader import StepLoaderService
from app.services.parts_extractor import PartsExtractorService
from app.services.svg_generator import SvgGeneratorService
from app.services.assembly_generator import AssemblyGeneratorService
from app.services.llm_assembly_generator import LLMAssemblyGeneratorService
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """
    Orchestrates the full 4-stage processing pipeline:

    Stage 1: STEP Loading (file → geometry)
    Stage 2: Parts Extraction (geometry → parts)
    Stage 3: SVG Generation (parts → drawings)
    Stage 4: Assembly Generation (parts + drawings → steps)

    Each stage emits rich progress updates including:
    - stage: Current processing stage
    - percentage: Overall progress (0-100%)
    - action: Detailed action description
    - eta_seconds: Estimated time remaining
    """

    def __init__(self, container: ServiceContainer) -> None:
        self.container = container
        self.logger = logging.getLogger(__name__)

        # Initialize services
        self.step_loader = StepLoaderService()
        self.parts_extractor = PartsExtractorService()
        self.svg_generator = SvgGeneratorService()

        # Initialize LLM service for Phase 3
        llm_service = None
        if settings.assembly_llm_enabled:
            llm_service = LLMAssemblyGeneratorService()
            self.logger.info("LLM-powered assembly generation enabled (Phase 3)")
        else:
            self.logger.info("LLM-powered assembly generation disabled, using rules-based fallback")

        # Inject LLM service into assembly generator
        self.assembly_generator = AssemblyGeneratorService(llm_service=llm_service)

    async def process_step_file(self, model_id: str, file_content: bytes, job_id: str) -> None:
        """
        Run the full pipeline as a background task.

        Updates job status and emits progress via SSE at each stage.

        Args:
            model_id: UUID of the model
            file_content: Raw STEP file bytes
            job_id: UUID of the processing job
        """
        repository = await self.container.get_repository()
        progress_tracker = await self.container.get_progress_tracker()

        try:
            # ========== STAGE 1: Load STEP File ==========
            self.logger.info(f"[{job_id}] Starting Stage 1: STEP Loading")

            await repository.update_job(
                job_id,
                status=ProcessingStatus.PROCESSING,
                progress_percent=0,
                current_stage="loading_geometry",
                action="Initializing STEP file parsing...",
                eta_seconds=60,
            )

            await progress_tracker.emit(
                job_id,
                ProgressEvent(
                    stage="loading_geometry",
                    status="processing",
                    percentage=5,
                    message="Initializing STEP file parsing...",
                    data={"eta_seconds": 60},
                ),
            )

            geometry = await asyncio.wait_for(
                self.step_loader.process(file_content),
                timeout=settings.step_processing_timeout_seconds,
            )
            await repository.save_geometry(model_id, geometry)

            await repository.update_job(
                job_id,
                progress_percent=25,
                current_stage="loading_geometry",
                action=f"Loaded {len(geometry.vertices)} vertices",
                eta_seconds=45,
            )

            await progress_tracker.emit(
                job_id,
                ProgressEvent(
                    stage="loading_geometry",
                    status="complete",
                    percentage=25,
                    message=f"Loaded {len(geometry.vertices)} vertices from STEP file",
                    data={"eta_seconds": 45},
                ),
            )
            self.logger.info(f"[{job_id}] Stage 1 complete: {len(geometry.vertices)} vertices")

            # ========== STAGE 2: Extract Parts ==========
            self.logger.info(f"[{job_id}] Starting Stage 2: Parts Extraction")

            await repository.update_job(
                job_id,
                progress_percent=25,
                current_stage="extracting_parts",
                action="Extracting and classifying parts...",
                eta_seconds=30,
            )

            await progress_tracker.emit(
                job_id,
                ProgressEvent(
                    stage="extracting_parts",
                    status="processing",
                    percentage=30,
                    message="Extracting and classifying parts...",
                    data={"eta_seconds": 30},
                ),
            )

            parts = await asyncio.wait_for(
                self.parts_extractor.process(geometry),
                timeout=settings.svg_generation_timeout_seconds,
            )
            await repository.save_parts(model_id, parts)

            await repository.update_job(
                job_id,
                progress_percent=50,
                current_stage="extracting_parts",
                action=f"Extracted {len(parts)} parts",
                eta_seconds=20,
            )

            await progress_tracker.emit(
                job_id,
                ProgressEvent(
                    stage="extracting_parts",
                    status="complete",
                    percentage=50,
                    message=f"Extracted {len(parts)} parts, classified into categories",
                    data={"eta_seconds": 20},
                ),
            )
            self.logger.info(f"[{job_id}] Stage 2 complete: {len(parts)} parts")

            # ========== STAGE 3: Generate SVG Drawings ==========
            self.logger.info(f"[{job_id}] Starting Stage 3: SVG Generation")

            await repository.update_job(
                job_id,
                progress_percent=50,
                current_stage="generating_svgs",
                action="Generating technical drawings...",
                eta_seconds=20,
            )

            await progress_tracker.emit(
                job_id,
                ProgressEvent(
                    stage="generating_svgs",
                    status="processing",
                    percentage=60,
                    message="Generating isometric technical drawings...",
                    data={"eta_seconds": 20},
                ),
            )

            drawings = await asyncio.wait_for(
                self.svg_generator.process(parts),
                timeout=settings.svg_generation_timeout_seconds,
            )
            await repository.save_drawings(model_id, drawings)

            await repository.update_job(
                job_id,
                progress_percent=75,
                current_stage="generating_svgs",
                action=f"Generated {len(drawings)} SVG drawings",
                eta_seconds=10,
            )

            await progress_tracker.emit(
                job_id,
                ProgressEvent(
                    stage="generating_svgs",
                    status="complete",
                    percentage=75,
                    message=f"Generated {len(drawings)} SVG drawings",
                    data={"eta_seconds": 10},
                ),
            )
            self.logger.info(f"[{job_id}] Stage 3 complete: {len(drawings)} drawings")

            # ========== STAGE 4: Generate Assembly Instructions ==========
            self.logger.info(f"[{job_id}] Starting Stage 4: Assembly Generation")

            await repository.update_job(
                job_id,
                progress_percent=75,
                current_stage="generating_assembly",
                action="Generating assembly instructions...",
                eta_seconds=10,
            )

            await progress_tracker.emit(
                job_id,
                ProgressEvent(
                    stage="generating_assembly",
                    status="processing",
                    percentage=80,
                    message="Analyzing parts and generating assembly sequence...",
                    data={"eta_seconds": 10},
                ),
            )

            steps = await asyncio.wait_for(
                self.assembly_generator.process(parts, drawings, preview_only=False),
                timeout=settings.assembly_generation_timeout_seconds,
            )
            await repository.save_steps(model_id, steps)

            await repository.update_job(
                job_id,
                progress_percent=95,
                current_stage="generating_assembly",
                action=f"Generated {len(steps)} assembly steps",
                eta_seconds=2,
            )

            await progress_tracker.emit(
                job_id,
                ProgressEvent(
                    stage="generating_assembly",
                    status="complete",
                    percentage=95,
                    message=f"Generated {len(steps)} assembly steps",
                    data={"eta_seconds": 2},
                ),
            )
            self.logger.info(f"[{job_id}] Stage 4 complete: {len(steps)} steps")

            # ========== COMPLETION ==========
            await repository.update_job(
                job_id,
                status=ProcessingStatus.COMPLETE,
                progress_percent=100,
                current_stage="complete",
                action="Pipeline completed successfully",
                eta_seconds=0,
            )

            await progress_tracker.emit(
                job_id,
                ProgressEvent(
                    stage="complete",
                    status="success",
                    percentage=100,
                    message="All processing stages completed successfully",
                    data={"eta_seconds": 0},
                ),
            )

            self.logger.info(f"[{job_id}] Pipeline completed successfully")

        except asyncio.TimeoutError as e:
            error_msg = f"Processing timeout: {str(e)}"
            self.logger.error(f"[{job_id}] {error_msg}")
            await repository.update_job(
                job_id,
                status=ProcessingStatus.FAILED,
                error_message=error_msg,
            )
            await progress_tracker.emit(
                job_id,
                ProgressEvent(
                    stage="error",
                    status="failed",
                    percentage=0,
                    message=error_msg,
                    data={"error_message": error_msg},
                ),
            )

        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            self.logger.exception(f"[{job_id}] {error_msg}")
            await repository.update_job(
                job_id,
                status=ProcessingStatus.FAILED,
                error_message=error_msg,
            )
            await progress_tracker.emit(
                job_id,
                ProgressEvent(
                    stage="error",
                    status="failed",
                    percentage=0,
                    message=error_msg,
                    data={"error_message": error_msg},
                ),
            )
