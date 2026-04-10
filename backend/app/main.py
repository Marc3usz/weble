"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import CADProcessingError
from app.container import get_container
from app.api.v1.endpoints import health, step, jobs


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    # Setup logging
    logging.basicConfig(
        level=settings.log_level.value,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    # ========== Lifespan Events ==========

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manage application startup and shutdown."""
        # Startup
        logger.info("Starting WEBLE backend...")
        container = await get_container()
        logger.info("Services initialized")

        yield

        # Shutdown
        logger.info("Shutting down WEBLE backend...")

    app = FastAPI(
        title="WEBLE Backend",
        description="AI-Powered STEP to IKEA Assembly Instructions",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    # ========== CORS Middleware ==========
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ========== Exception Handlers ==========

    @app.exception_handler(CADProcessingError)
    async def cad_error_handler(request, exc: CADProcessingError):
        """Handle CAD processing errors."""
        return JSONResponse(
            status_code=400,
            content={
                "error": exc.code,
                "message": exc.message,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request, exc: RequestValidationError):
        """Handle validation errors."""
        return JSONResponse(
            status_code=422,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request, exc: Exception):
        """Handle unexpected errors."""
        logger.exception("Unexpected error")
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            },
        )

    # ========== Include Routers ==========

    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(step.router, prefix="/api/v1", tags=["step"])
    app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])

    return app


# Create app instance
app = create_app()
