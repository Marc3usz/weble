# WEBLE Backend

AI-Powered STEP to IKEA Assembly Instructions - Backend API

## Overview

This is the FastAPI backend for WEBLE that processes CAD files (STEP/STP format) and generates IKEA-style assembly instructions.

## Development Setup

### Prerequisites

- Python 3.10+
- uv (Python package manager)

### Installation

```bash
# Create virtual environment
uv venv

# Activate it
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On macOS/Linux

# Install dependencies
uv pip install -e .

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

## API Endpoints

- `POST /api/v1/step/upload` - Upload and process STEP file
- `GET /api/v1/jobs/{job_id}` - Get job status
- `GET /api/v1/jobs/{job_id}/sse` - Stream job progress (SSE)
- `GET /api/v1/health` - Health check

## Architecture

The backend implements a 4-stage pipeline:

1. **Stage 1**: STEP Loading - Load CAD file and extract 3D geometry
2. **Stage 2**: Parts Extraction - Extract and classify parts
3. **Stage 3**: SVG Generation - Generate 2D technical drawings
4. **Stage 4**: Assembly Generation - Generate assembly instructions

## Development

The backend currently uses in-memory storage for development. Migration to PostgreSQL is straightforward using the database adapter pattern.

### Running Tests

```bash
pytest
```

## License

MIT
