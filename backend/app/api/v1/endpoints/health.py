"""Health check endpoints."""

from fastapi import APIRouter

from app.models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", message="WEBLE backend is running")


@router.get("/health/detailed")
async def health_check_detailed() -> dict:
    """Detailed health check with service status."""
    return {
        "status": "healthy",
        "services": {
            "api": "healthy",
            "database": "healthy (in-memory)",
            "storage": "healthy (local)",
        },
    }
