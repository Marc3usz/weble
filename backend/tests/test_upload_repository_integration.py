"""Tests for STEP upload endpoint and repository integration."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.container import reset_container
from app.db.factory import reset_repository


@pytest.fixture
async def cleanup():
    """Clean up before and after each test."""
    await reset_repository()
    await reset_container()
    yield
    await reset_repository()
    await reset_container()


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


class TestStepUploadEndpoint:
    """Test STEP file upload endpoint with repository pattern."""

    @pytest.mark.asyncio
    async def test_upload_step_file(self, client: TestClient, cleanup):
        """Test uploading a valid STEP file."""
        # Create a minimal STEP file
        step_content = b"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Test STEP file'),
'2;1','','');
FILE_NAME('test.step','2024-04-17T00:00:00',('User'),(''),
'','','');
FILE_SCHEMA(('AP214'));
ENDSEC;
DATA;
ENDSEC;
END-ISO-10303-21;
"""

        response = client.post(
            "/api/v1/step/upload",
            files={"file": ("test.step", step_content, "application/octet-stream")},
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "model_id" in data
        assert data["status"] == "processing"
        assert "estimated_time_seconds" in data

    @pytest.mark.asyncio
    async def test_upload_empty_file(self, client: TestClient, cleanup):
        """Test uploading an empty file."""
        response = client.post(
            "/api/v1/step/upload",
            files={"file": ("empty.step", b"", "application/octet-stream")},
        )

        assert response.status_code == 400  # Bad request

    @pytest.mark.asyncio
    async def test_upload_invalid_file_content(self, client: TestClient, cleanup):
        """Test uploading file with invalid content."""
        response = client.post(
            "/api/v1/step/upload",
            files={
                "file": ("invalid.step", b"This is not a STEP file", "application/octet-stream")
            },
        )

        assert response.status_code == 400  # Bad request

    @pytest.mark.asyncio
    async def test_upload_oversized_file(self, client: TestClient, cleanup):
        """Test uploading file larger than max size."""
        # Create file larger than 50 MB
        large_content = b"x" * (51 * 1024 * 1024 + 1)

        response = client.post(
            "/api/v1/step/upload",
            files={"file": ("large.step", large_content, "application/octet-stream")},
        )

        assert response.status_code == 400  # Bad request (file too large)

    @pytest.mark.asyncio
    async def test_get_model_status(self, client: TestClient, cleanup):
        """Test getting model status after upload."""
        # Create a minimal STEP file
        step_content = b"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Test STEP file'),
'2;1','','');
FILE_NAME('test.step','2024-04-17T00:00:00',('User'),(''),
'','','');
FILE_SCHEMA(('AP214'));
ENDSEC;
DATA;
ENDSEC;
END-ISO-10303-21;
"""

        # Upload file
        response = client.post(
            "/api/v1/step/upload",
            files={"file": ("test.step", step_content, "application/octet-stream")},
        )
        upload_data = response.json()
        model_id = upload_data["model_id"]

        # Get model status
        response = client.get(f"/api/v1/step/{model_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["model_id"] == model_id
        assert "file_name" in data
        assert "file_size" in data
        assert "geometry_loaded" in data

    @pytest.mark.asyncio
    async def test_get_nonexistent_model(self, client: TestClient, cleanup):
        """Test getting status of non-existent model."""
        response = client.get("/api/v1/step/nonexistent-model-id")
        assert response.status_code == 200

        data = response.json()
        assert "error" in data or "model_id" in data

    @pytest.mark.asyncio
    async def test_get_job_status(self, client: TestClient, cleanup):
        """Test getting job status."""
        step_content = b"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Test STEP file'),
'2;1','','');
FILE_NAME('test.step','2024-04-17T00:00:00',('User'),(''),
'','','');
FILE_SCHEMA(('AP214'));
ENDSEC;
DATA;
ENDSEC;
END-ISO-10303-21;
"""

        # Upload file
        response = client.post(
            "/api/v1/step/upload",
            files={"file": ("test.step", step_content, "application/octet-stream")},
        )
        job_id = response.json()["job_id"]

        # Get job status
        response = client.get(f"/api/v1/jobs/{job_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["job_id"] == job_id
        assert "status" in data
        assert "progress_percent" in data
        assert "current_stage" in data


class TestRepositoryIntegration:
    """Test repository integration with endpoints."""

    @pytest.mark.asyncio
    async def test_repository_persists_model_data(self, client: TestClient, cleanup):
        """Test that repository persists model data correctly."""
        from app.container import get_container

        step_content = b"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Test STEP file'),
'2;1','','');
FILE_NAME('test.step','2024-04-17T00:00:00',('User'),(''),
'','','');
FILE_SCHEMA(('AP214'));
ENDSEC;
DATA;
ENDSEC;
END-ISO-10303-21;
"""

        # Upload file
        response = client.post(
            "/api/v1/step/upload",
            files={"file": ("test.step", step_content, "application/octet-stream")},
        )
        model_id = response.json()["model_id"]

        # Get repository and verify model was created
        container = await get_container()
        repository = await container.get_repository()

        model = await repository.get_model(model_id)
        assert model is not None
        assert model["file_name"] == "test.step"
        assert model["file_size"] == len(step_content)

    @pytest.mark.asyncio
    async def test_repository_persists_job_status(self, client: TestClient, cleanup):
        """Test that repository persists job status correctly."""
        from app.container import get_container

        step_content = b"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Test STEP file'),
'2;1','','');
FILE_NAME('test.step','2024-04-17T00:00:00',('User'),(''),
'','','');
FILE_SCHEMA(('AP214'));
ENDSEC;
DATA;
ENDSEC;
END-ISO-10303-21;
"""

        # Upload file
        response = client.post(
            "/api/v1/step/upload",
            files={"file": ("test.step", step_content, "application/octet-stream")},
        )
        job_id = response.json()["job_id"]

        # Get repository and verify job was created
        container = await get_container()
        repository = await container.get_repository()

        job = await repository.get_job(job_id)
        assert job is not None
        # Job could be processing or complete depending on timing
        assert job.status.value in ["processing", "complete", "failed"]
