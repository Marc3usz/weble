# WEBLE Backend API - Comprehensive Analysis

## Executive Summary

The WEBLE backend is a Python FastAPI application that processes STEP CAD files through a 4-stage pipeline and generates IKEA-style assembly instructions.

**Key Information:**
- Framework: FastAPI with async/await support
- Database: In-memory (default), SQLite, or PostgreSQL
- Authentication: None (CORS allows all origins for development)
- SSE: Server-Sent Events for real-time progress tracking
- Framework Version: FastAPI >=0.104.0, Uvicorn >=0.24.0

## Architecture Overview

### Processing Pipeline (4 Stages)

Stage 1: STEP Loading → Geometry3D (vertices, normals, indices)
Stage 2: Parts Extraction → Parts[] (classified, deduplicated)
Stage 3: SVG Generation → SvgDrawing[] (technical drawings)
Stage 4: Assembly Gen → AssemblyStep[] (instructions)

## API Endpoints Summary

### 1. POST /api/v1/step/upload
Upload and process a STEP file (asynchronous)

**Request:** multipart/form-data with "file" field
**File Requirements:**
- Must start with magic bytes: ISO-10303-21
- Minimum size: 100 bytes
- Maximum size: 50 MB (configurable)

**Response (200 OK):**
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "model_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "status": "processing",
  "estimated_time_seconds": 60
}

Fields:
- job_id: str (UUID of processing job)
- model_id: str (UUID of CAD model)
- status: str ("processing")
- estimated_time_seconds: int (always 60)

**Error Codes:**
- 400 INVALID_STEP_FILE: File format invalid
- 400 FILE_TOO_LARGE: Exceeds max size
- 422 VALIDATION_ERROR: Missing file

**Behavior:** Returns immediately, triggers background pipeline

### 2. GET /api/v1/step/progress/{job_id}/stream
Real-time progress streaming via Server-Sent Events

**Response:** SSE stream with JSON events

Event structure:
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress_percent": 25,
  "current_stage": "loading_geometry",
  "action": "Loaded 1024 vertices from STEP file",
  "eta_seconds": 45,
  "error_message": null,
  "timestamp": null
}

Fields:
- job_id: str
- status: str ("processing", "complete", "failed")
- progress_percent: int (0-100)
- current_stage: str (stage name)
- action: str (detailed action)
- eta_seconds: int
- error_message: Optional[str]
- timestamp: Optional[str]

Stages and percentages:
- loading_geometry (0-25%): STEP file parsing
- extracting_parts (25-50%): Part classification
- generating_svgs (50-75%): Technical drawing generation
- generating_assembly (75-95%): Assembly instruction generation
- complete (100%): Pipeline finished

Status values:
- processing: Currently executing
- complete: Successfully finished
- failed: Error occurred
- success: Final success (internal only)

### 3. GET /api/v1/jobs/{job_id}
Get current job status (single request, not streaming)

**Response (200 OK):**
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "model_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "status": "processing",
  "progress_percent": 50,
  "current_stage": "extracting_parts",
  "action": "Extracted 42 parts",
  "eta_seconds": 20,
  "error_message": null
}

Status enum values:
- pending: Created, not started
- processing: Currently executing
- complete: Successfully finished
- failed: Error occurred

**Error Response (404):**
{
  "detail": "Job not found"
}

### 4. GET /api/v1/step/{model_id}
Get processed STEP model geometry

**Response (200 OK):**
{
  "status": "success",
  "model_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "file_name": "part.step",
  "file_size": 102400,
  "geometry_loaded": true,
  "geometry": {
    "vertices": [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], ...],
    "normals": [[0.0, 0.0, -1.0], [0.0, 0.0, 1.0], ...],
    "indices": [0, 1, 2, 0, 2, 3, ...],
    "metadata": {
      "solids": [{
        "bounding_box": {"min": [0.0, 0.0, 0.0], "max": [10.0, 10.0, 10.0]},
        "centroid": [5.0, 5.0, 5.0],
        "volume": 1000.0,
        "surface_area": 600.0
      }]
    }
  }
}

Geometry details:
- vertices: List[List[float]] - Triangle mesh vertices (x, y, z)
- normals: List[List[float]] - Surface normals (nx, ny, nz)
- indices: List[int] - Triangle indices (groups of 3)
- metadata.solids: Solid objects with bounding boxes, centroids, volume, surface area

### 5. POST /api/v1/step/parts-2d
Get or extract parts from a model

**Request Body:**
{
  "model_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
}

Accepted field names: model_id or modelId

**Response (200 OK):**
{
  "model_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "parts": [
    {
      "id": "A",
      "part_type": "panel",
      "quantity": 2,
      "volume": 1500.5,
      "dimensions": {"width": 100.0, "height": 50.0, "depth": 2.0}
    },
    {
      "id": "B",
      "part_type": "fastener",
      "quantity": 8,
      "volume": 12.5,
      "dimensions": {"width": 5.0, "height": 5.0, "depth": 0.5}
    }
  ],
  "total_parts": 2
}

Part type values:
- panel: Large surface area, thin (width/height >> depth)
- hardware: Bolts, washers, nuts
- fastener: Screws, rivets
- structural: Bracing, support
- other: Unclassified

### 6. POST /api/v1/step/assembly-analysis
Get or generate assembly instructions

**Request Body:**
{
  "model_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "preview_only": false
}

Accepted field names: model_id or modelId

**Response (200 OK):**
{
  "model_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "steps": [
    {
      "step_number": 1,
      "title": "Prepare base panels",
      "description": "Assemble the left and right side panels with corner brackets",
      "detail_description": "First, gather the left panel (A) and right panel (B). Align them at a 90-degree angle...",
      "part_indices": [0, 1],
      "part_roles": {"0": "left_side", "1": "right_side"},
      "context_part_indices": [3],
      "duration_minutes": 5,
      "assembly_sequence": ["Align", "Insert brackets", "Secure bolts"],
      "warnings": ["Ensure panel edges are flush", "Do not over-tighten bolts"],
      "tips": ["Use level to ensure panels are square"],
      "confidence_score": 0.95,
      "is_llm_generated": true
    }
  ],
  "total_steps": 1
}

Phase 3 (LLM) Fields:
- detail_description: Expanded step description from LLM
- assembly_sequence: Step-by-step sub-actions
- warnings: Safety/caution messages
- tips: Helpful user guidance
- confidence_score: LLM confidence (0-1, default 0.8 for rules-based)
- is_llm_generated: True if from LLM, false if rules-based

Processing modes:
- preview_only=true: Returns fast, simplified steps (rules-based only)
- assembly_llm_enabled=true: Attempts LLM generation first
- Falls back to rules-based if LLM fails

LLM Configuration:
- assembly_llm_model: "google/gemini-2.0-flash"
- assembly_tone: "ikea", "technical", or "beginner"

### 7. GET /api/v1/health
Health check endpoint

**Response (200 OK):**
{
  "status": "healthy",
  "version": "0.1.0",
  "message": "API is healthy"
}

### 8. GET /api/v1/health/detailed
Detailed health check

**Response (200 OK):**
{
  "status": "healthy",
  "services": {
    "api": "healthy",
    "database": "healthy (in-memory)",
    "storage": "healthy (local)"
  }
}

## Error Response Format

Standard error response (400/422/500):
{
  "error": "ERROR_CODE",
  "message": "Human readable error message",
  "details": []
}

Error codes:
- INVALID_STEP_FILE: File format invalid
- FILE_TOO_LARGE: Exceeds max size
- NO_SOLIDS_FOUND: No geometry in STEP
- PART_EXTRACTION_ERROR: Failed extracting part
- SVG_GENERATION_ERROR: Failed generating SVG
- LLM_API_ERROR: OpenRouter API failure
- ASSEMBLY_VALIDATION_ERROR: Generated assembly invalid
- VALIDATION_ERROR: Request validation failed
- INTERNAL_ERROR: Unexpected server error

## Data Transformations

### Stage 1: STEP File → Geometry3D
Input: Raw STEP file bytes
- Must start with: ISO-10303-21
- Minimum size: 100 bytes

Processing:
1. Try CadQuery library (if available)
2. Fallback: STEP text parser

Output: Geometry3D
{
  "vertices": List[List[float]],
  "normals": List[List[float]],
  "indices": List[int],
  "metadata": {
    "solids": [{
      "bounding_box": {"min": [...], "max": [...]},
      "centroid": [x, y, z],
      "volume": float,
      "surface_area": float
    }, ...]
  }
}

### Stage 2: Geometry3D → Parts[]
Input: Geometry3D with solids metadata

Processing:
1. Extract solid metadata
2. Compute dimensions (width, height, depth)
3. Classify each solid
4. Deduplicate similar parts (adaptive tolerance 5-30%)

Output: Parts[]
{
  "id": "A",
  "original_index": 0,
  "part_type": PartType,
  "quantity": int,
  "volume": float,
  "dimensions": {"width": float, "height": float, "depth": float},
  "centroid": [x, y, z],
  "surface_area": float,
  "group_id": str,
  "metrics": {}
}

### Stage 3: Parts[] → SvgDrawing[]
Input: Parts with dimensions

Processing:
1. Generate technical drawing for each part
2. Orthographic projections (front, side, top)
3. Isometric 3D view
4. Dimension annotations
5. Render to SVG

Output: SvgDrawing[]
{
  "part_id": "A",
  "svg_content": "<svg>...</svg>",
  "quantity_label": "Qty: 2",
  "metadata": {}
}

### Stage 4: (Parts[], SvgDrawing[]) → AssemblyStep[]
Input: Parts and SvgDrawings

Processing - Option A (Rules-Based):
1. Sort parts by assembly difficulty
2. Group by type
3. Generate step sequence
4. Add duration estimates
5. Generate exploded view diagrams

Processing - Option B (LLM-Powered, if enabled):
1. Create detailed context from parts and drawings
2. Call OpenRouter Gemini 2.0 Flash API
3. LLM generates:
   - Step descriptions (detail_description)
   - Assembly sequences (assembly_sequence)
   - Safety warnings (warnings)
   - Helpful tips (tips)
   - Confidence scores
4. Add exploded view SVG to each step

Output: AssemblyStep[]
{
  "step_number": int,
  "title": str,
  "description": str,
  "detail_description": str,
  "part_indices": List[int],
  "part_roles": Dict[int, str],
  "context_part_indices": List[int],
  "duration_minutes": int,
  "assembly_sequence": List[str],
  "warnings": List[str],
  "tips": List[str],
  "confidence_score": float,
  "is_llm_generated": bool
}

## Request/Response Field Mapping

Frontend field names → Backend field names:
- modelId → model_id (POST parts-2d, assembly-analysis)
- model_id → model_id (direct)
- job_id → {job_id} (path parameter)
- file → File upload (multipart)

Backend field names → Frontend usage:
- job_id → used in progress tracking
- model_id → used throughout
- status → progress status
- progress_percent → percentage display
- current_stage → stage display
- part_type → part type display
- is_llm_generated → quality indicator
- confidence_score → quality indicator

## Configuration

Core settings (app/core/config.py):
- debug: bool = False
- log_level: LogLevel = LogLevel.INFO
- host: str = "0.0.0.0"
- port: int = 8000

Database:
- database_type: DatabaseType = DatabaseType.MEMORY
- database_url: str = ""
- database_pool_size: int = 10

File Storage:
- storage_type: StorageType = StorageType.LOCAL
- local_storage_path: str = "./storage"
- max_file_size_mb: int = 50
- max_parts_per_model: int = 500

Timeouts (seconds):
- step_processing_timeout_seconds: int = 300 (5 min)
- svg_generation_timeout_seconds: int = 60
- assembly_generation_timeout_seconds: int = 120
- llm_timeout_seconds: int = 30

LLM:
- assembly_llm_enabled: bool = True
- assembly_tone: AssemblyTone = AssemblyTone.IKEA
- assembly_llm_model: str = "google/gemini-2.0-flash"
- llm_max_tokens: int = 2000

SSE:
- sse_heartbeat_seconds: int = 2
- job_retention_hours: int = 24

## Authentication & CORS

CORS Configuration:
- allow_origins: ["*"] (all origins, development mode)
- allow_credentials: True
- allow_methods: ["*"]
- allow_headers: ["*"]

Authentication: None required (no API key or JWT)

## Known Inconsistencies

1. Field Name Variations
   - Parts-2d and assembly-analysis accept both model_id and modelId
   - Backend normalizes: payload.get("modelId") or payload.get("model_id")

2. Endpoint Path Inconsistency
   - Primary: GET /api/v1/step/progress/{job_id}/stream
   - Alternative: GET /api/v1/jobs/{job_id}/sse
   - Frontend uses primary endpoint

3. Status Values Mismatch
   - SSE events use "success" for completion
   - Status enum uses "complete"
   - Mapped in response serialization

4. Geometry Response Format
   - GET /api/v1/step/{model_id} wraps geometry in response object
   - Geometry3D stores it flat internally
   - Manual wrapping in endpoint response

5. SSE Event Field Mapping
   - Internal ProgressEvent: stage, status, percentage, message
   - API ProgressStreamResponse: current_stage, status, progress_percent, action
   - Transformation in stream_progress endpoint (lines 306-315 of step.py)

## Summary Table

| Endpoint | Method | Purpose | Auth | Async |
|---|---|---|---|---|
| /api/v1/step/upload | POST | Upload STEP file | None | Yes |
| /api/v1/step/progress/{jobId}/stream | GET | SSE progress | None | Yes |
| /api/v1/jobs/{jobId} | GET | Job status | None | No |
| /api/v1/step/{modelId} | GET | Geometry data | None | No |
| /api/v1/step/parts-2d | POST | Parts extraction | None | No |
| /api/v1/step/assembly-analysis | POST | Assembly gen | None | No |
| /api/v1/health | GET | Health check | None | No |
| /api/v1/health/detailed | GET | Detailed health | None | No |

Document Version: 1.0
Last Updated: April 19, 2026
Backend Version: 0.1.0
Framework: FastAPI >= 0.104.0
