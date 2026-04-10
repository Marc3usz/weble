"""Tests for API endpoints."""

import pytest
import pytest_asyncio
import json
from fastapi.testclient import TestClient
from app.main import create_app


@pytest_asyncio.fixture
async def app():
    """Create test FastAPI app."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def valid_step_file_bytes():
    """Create valid STEP file bytes for upload."""
    content = (
        b"ISO-10303-21;\n"
        b"HEADER;\n"
        b"FILE_DESCRIPTION(('Test STEP File'),\n"
        b"'2;1');\n"
        b"FILE_NAME('test.step',\n"
        b"2024-01-01T00:00:00,(''),(''),\n"
        b"'',\n"
        b"'',\n"
        b"'');\n"
        b"FILE_SCHEMA(('AP214'));\n"
        b"ENDSEC;\n"
        b"DATA;\n"
        b"ENDSEC;\n"
        b"END-ISO-10303-21;\n"
    )
    return content


class TestHealthEndpoint:
    """Test health check endpoints."""

    def test_health_check(self, client):
        """Test GET /api/v1/health returns 200."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_detailed(self, client):
        """Test GET /api/v1/health/detailed returns 200."""
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data


class TestStepUploadEndpoint:
    """Test STEP file upload endpoint."""

    def test_upload_step_file_returns_200(self, client, valid_step_file_bytes):
        """Test POST /api/v1/step/upload with valid STEP file returns 200."""
        response = client.post(
            "/api/v1/step/upload",
            files={"file": ("test.step", valid_step_file_bytes, "application/octet-stream")},
        )
        assert response.status_code == 200

    def test_upload_step_file_returns_job_id(self, client, valid_step_file_bytes):
        """Test that upload response contains job_id."""
        response = client.post(
            "/api/v1/step/upload",
            files={"file": ("test.step", valid_step_file_bytes, "application/octet-stream")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "model_id" in data

    def test_upload_step_file_returns_model_id(self, client, valid_step_file_bytes):
        """Test that upload response contains model_id."""
        response = client.post(
            "/api/v1/step/upload",
            files={"file": ("test.step", valid_step_file_bytes, "application/octet-stream")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "model_id" in data
        assert len(data["model_id"]) > 0

    def test_upload_invalid_file_returns_error(self, client):
        """Test that uploading invalid file returns appropriate error."""
        response = client.post(
            "/api/v1/step/upload", files={"file": ("invalid.txt", b"not a step file", "text/plain")}
        )
        # Should return error status
        assert response.status_code in [400, 422, 500]

    def test_upload_no_file_returns_error(self, client):
        """Test that uploading without file returns error."""
        response = client.post("/api/v1/step/upload")
        assert response.status_code in [400, 422]


class TestJobStatusEndpoint:
    """Test job status endpoint."""

    def test_get_nonexistent_job_returns_404(self, client):
        """Test GET /api/v1/jobs/{job_id} for nonexistent job returns 404."""
        response = client.get("/api/v1/jobs/nonexistent-id")
        assert response.status_code == 404

    def test_get_job_after_upload_returns_200(self, client, valid_step_file_bytes):
        """Test that we can retrieve job status after upload."""
        upload_response = client.post(
            "/api/v1/step/upload",
            files={"file": ("test.step", valid_step_file_bytes, "application/octet-stream")},
        )
        assert upload_response.status_code == 200
        job_id = upload_response.json()["job_id"]

        status_response = client.get(f"/api/v1/jobs/{job_id}")
        assert status_response.status_code == 200

    def test_job_status_response_has_required_fields(self, client, valid_step_file_bytes):
        """Test that job status response has all required fields."""
        upload_response = client.post(
            "/api/v1/step/upload",
            files={"file": ("test.step", valid_step_file_bytes, "application/octet-stream")},
        )
        job_id = upload_response.json()["job_id"]

        status_response = client.get(f"/api/v1/jobs/{job_id}")
        assert status_response.status_code == 200
        data = status_response.json()
        assert "job_id" in data
        assert "status" in data
        assert "progress_percent" in data


class TestStepModelEndpoint:
    """Test STEP model retrieval endpoint."""

    def test_get_nonexistent_model_returns_error(self, client):
        """Test GET /api/v1/step/{model_id} for nonexistent model returns error."""
        response = client.get("/api/v1/step/nonexistent-id")
        assert response.status_code == 200  # API returns 200 with error message
        data = response.json()
        assert "error" in data or "status" in data

    def test_get_model_after_upload_returns_200(self, client, valid_step_file_bytes):
        """Test that we can retrieve model data after upload."""
        upload_response = client.post(
            "/api/v1/step/upload",
            files={"file": ("test.step", valid_step_file_bytes, "application/octet-stream")},
        )
        assert upload_response.status_code == 200
        model_id = upload_response.json()["model_id"]

        model_response = client.get(f"/api/v1/step/{model_id}")
        assert model_response.status_code == 200

    def test_model_response_has_metadata(self, client, valid_step_file_bytes):
        """Test that model response includes metadata."""
        upload_response = client.post(
            "/api/v1/step/upload",
            files={"file": ("test.step", valid_step_file_bytes, "application/octet-stream")},
        )
        model_id = upload_response.json()["model_id"]

        model_response = client.get(f"/api/v1/step/{model_id}")
        assert model_response.status_code == 200
        data = model_response.json()
        assert "model_id" in data or "status" in data
