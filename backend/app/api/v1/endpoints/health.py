"""Health check endpoints."""

from fastapi import APIRouter

from app.models.schemas import HealthResponse
from app.utils.test_runner import TestRunner

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


@router.get("/health/tests")
async def run_tests() -> dict:
    """
    TEMPORARY ENDPOINT: Run all backend tests and return results.

    This endpoint will be removed once we have proper test infrastructure.
    """
    runner = TestRunner()
    results = runner.run_all_tests()

    return {
        "status": 200 if results.get("status") == "success" else 500,
        "http_status": 200,
        "test_results": {
            "passed": results.get("passed", 0),
            "failed": results.get("failed", 0),
            "errors": results.get("errors", 0),
            "skipped": results.get("skipped", 0),
            "total": results.get("total", 0),
            "summary": f"{results.get('passed', 0)} passed, {results.get('failed', 0)} failed",
        },
        "tests": results.get("tests", []),
    }


@router.get("/health/tests/{test_module}")
async def run_specific_test_module(test_module: str) -> dict:
    """
    TEMPORARY ENDPOINT: Run tests for a specific module.

    Test modules: test_step_loader, test_parts_extractor, test_svg_generator,
                  test_assembly_generator, test_api_endpoints
    """
    runner = TestRunner()
    results = runner.run_specific_test_module(test_module)

    return {
        "status": 200 if results.get("status") == "success" else 500,
        "http_status": 200,
        "module": test_module,
        "test_results": {
            "passed": results.get("passed", 0),
            "failed": results.get("failed", 0),
            "errors": results.get("errors", 0),
            "total": results.get("total", 0),
            "summary": f"{results.get('passed', 0)} passed, {results.get('failed', 0)} failed",
        },
        "tests": results.get("tests", []),
    }


@router.get("/health/tests/status")
async def infrastructure_status() -> dict:
    """
    TEMPORARY ENDPOINT: Get infrastructure status without running tests.

    This provides a summary of what test infrastructure is available
    without actually running tests (useful if pytest is not installed).
    """
    runner = TestRunner()
    status = runner.get_infrastructure_status()

    return {
        "status": 200,
        "http_status": 200,
        "infrastructure": status,
    }
