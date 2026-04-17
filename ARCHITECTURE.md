# WEBLE System Architecture

## Complete System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER BROWSER (CLIENT)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              NEXT.JS FRONTEND (PORT 3000)                │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │                                                          │  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │  PAGES                                          │    │  │
│  │  ├──────────────────────────────┬──────────────────┤    │  │
│  │  │ /upload                      │ File Upload Page │    │  │
│  │  │ /viewer/[modelId]            │ 3D Viewer        │    │  │
│  │  │ /parts/[modelId]             │ Parts List       │    │  │
│  │  │ /assembly/[modelId]          │ Instructions     │    │  │
│  │  └──────────────────────────────┴──────────────────┘    │  │
│  │                                                          │  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │  COMPONENTS                                     │    │  │
│  │  ├──────────────────────────────────────────────────┤    │  │
│  │  │ • GeometryViewer (Three.js/React Three Fiber)  │    │  │
│  │  │ • Upload UI (Dropzone)                         │    │  │
│  │  │ • Parts Grid                                   │    │  │
│  │  │ • Assembly Step Carousel                       │    │  │
│  │  │ • PDF Export                                   │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  │                                                          │  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │  SERVICES & STATE                              │    │  │
│  │  ├──────────────────────────────────────────────────┤    │  │
│  │  │ • API Service (axios)                          │    │  │
│  │  │ • Zustand Store (Global State)                 │    │  │
│  │  │ • Progress Hook (SSE)                          │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  │                                                          │  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │  UTILITIES                                      │    │  │
│  │  ├──────────────────────────────────────────────────┤    │  │
│  │  │ • PDF Generation (React PDF)                   │    │  │
│  │  │ • Type Definitions (Full TypeScript)           │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                 │
│                              ▼                                 │
│                    HTTP + SSE (WebSocket)                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ REST API Calls
                              │ (JSON)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SERVER (BACKEND)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         FASTAPI BACKEND (PORT 8000)                       │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │                                                          │  │
│  │  POST   /api/v1/step/upload        ────┐              │  │
│  │  GET    /api/v1/step/{model_id}    ─┐  │              │  │
│  │  GET    /api/v1/step/progress/{...} stream (SSE)      │  │
│  │  POST   /api/v1/step/parts-2d      ─┤  │              │  │
│  │  POST   /api/v1/step/assembly-...  ────┘              │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────┐    │  │
│  │  │  Processing Pipeline                           │    │  │
│  │  ├────────────────────────────────────────────────┤    │  │
│  │  │ 1. STEP Loading      → Geometry3D             │    │  │
│  │  │ 2. Parts Extraction  → List[Part]             │    │  │
│  │  │ 3. SVG Generation    → List[SvgDrawing]       │    │  │
│  │  │ 4. Assembly Gen      → List[AssemblyStep]     │    │  │
│  │  └────────────────────────────────────────────────┘    │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────┐    │  │
│  │  │  Services                                      │    │  │
│  │  ├────────────────────────────────────────────────┤    │  │
│  │  │ • StepLoaderService      (CadQuery)           │    │  │
│  │  │ • PartsExtractorService  (Classification)     │    │  │
│  │  │ • SvgGeneratorService    (HLR to SVG)         │    │  │
│  │  │ • AssemblyGeneratorService (AI + Rules)       │    │  │
│  │  └────────────────────────────────────────────────┘    │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────┐    │  │
│  │  │  Infrastructure                                │    │  │
│  │  ├────────────────────────────────────────────────┤    │  │
│  │  │ • Progress Tracker (SSE Broadcasting)         │    │  │
│  │  │ • Database (In-Memory or SQLite)              │    │  │
│  │  │ • Job Queue (AsyncIO)                         │    │  │
│  │  └────────────────────────────────────────────────┘    │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────┐    │  │
│  │  │  External Integrations                         │    │  │
│  │  ├────────────────────────────────────────────────┤    │  │
│  │  │ • Google Gemini API (Optional)                 │    │  │
│  │  │ • OpenRouter API (Optional)                    │    │  │
│  │  └────────────────────────────────────────────────┘    │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  DEPENDENCIES                                            │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ • CadQuery (OpenCASCADE Python bindings)               │  │
│  │ • NumPy (Numerical operations)                         │  │
│  │ • Pydantic (Data validation)                           │  │
│  │ • SQLAlchemy (Database ORM) - Optional                 │  │
│  │ • Alembic (Database migrations) - Optional             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Upload to Assembly Instructions Flow

```
1. USER UPLOADS FILE
   └─→ Frontend: /upload page
       └─→ Validates file (format, size)
           └─→ POST /api/v1/step/upload
               └─→ Backend: Creates job, starts processing
                   └─→ Returns: job_id, model_id

2. REAL-TIME PROGRESS STREAMING
   └─→ Frontend: GET /api/v1/step/progress/{job_id}/stream (SSE)
       └─→ Backend: Streams progress events
           ├─→ "Initializing STEP parser..." (10%)
           ├─→ "Loading geometry..." (30%)
           ├─→ "Triangulating mesh..." (60%)
           ├─→ "Extracting parts..." (80%)
           └─→ "Complete!" (100%)

3. MODEL VISUALIZATION
   └─→ Frontend: GET /api/v1/step/{model_id}
       └─→ Backend: Returns geometry (vertices, normals, indices)
           └─→ Frontend: Renders with Three.js in 3D viewer
               └─→ Shows IKEA-style isometric view

4. PARTS EXTRACTION
   └─→ Frontend: POST /api/v1/step/parts-2d (payload: {model_id})
       └─→ Backend: Extracts parts, classifies them
           └─→ Returns: List of parts with metadata
               └─→ Frontend: Displays parts grid

5. ASSEMBLY INSTRUCTIONS
   └─→ Frontend: POST /api/v1/step/assembly-analysis
       └─→ Backend: Generates assembly steps
           ├─→ Analyzes part relationships
           ├─→ Calls AI API if enabled
           └─→ Returns: List of assembly steps
               └─→ Frontend: Shows step carousel

6. PDF EXPORT
   └─→ Frontend: React PDF Renderer
       └─→ Generates PDF with all pages
           └─→ User downloads manual.pdf
```

## Request/Response Examples

### 1. Upload

```
REQUEST:
  POST /api/v1/step/upload
  Content-Type: multipart/form-data
  Body: [binary STEP file]

RESPONSE:
  {
    "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "model_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "processing",
    "estimated_time_seconds": 60
  }
```

### 2. Progress (SSE)

```
REQUEST:
  GET /api/v1/step/progress/f47ac10b-58cc-4372-a567-0e02b2c3d479/stream

RESPONSE (Server-Sent Events):
  data: {
    "job_id": "f47ac10b-...",
    "status": "processing",
    "progress_percent": 35,
    "current_stage": "loading_geometry",
    "action": "Parsing STEP file...",
    "eta_seconds": 45
  }
  
  data: {
    "job_id": "f47ac10b-...",
    "status": "processing",
    "progress_percent": 100,
    "current_stage": "complete",
    "action": "Processing complete!",
    "eta_seconds": 0
  }
```

### 3. Model Data

```
REQUEST:
  GET /api/v1/step/550e8400-e29b-41d4-a716-446655440000

RESPONSE:
  {
    "status": "success",
    "model_id": "550e8400-e29b-41d4-a716-446655440000",
    "file_name": "table.step",
    "file_size": 2048576,
    "geometry_loaded": true,
    "geometry": {
      "vertices": [[0, 0, 0], [1, 0, 0], ...],
      "normals": [[0, 0, 1], [0, 0, 1], ...],
      "indices": [0, 1, 2, 1, 2, 3, ...],
      "metadata": {}
    }
  }
```

### 4. Parts Extraction

```
REQUEST:
  POST /api/v1/step/parts-2d
  Content-Type: application/json
  {
    "model_id": "550e8400-e29b-41d4-a716-446655440000"
  }

RESPONSE:
  {
    "model_id": "550e8400-e29b-41d4-a716-446655440000",
    "parts": [
      {
        "id": "A",
        "part_type": "panel",
        "quantity": 2,
        "volume": 5000.0,
        "dimensions": {"width": 100, "height": 50, "depth": 2}
      },
      {
        "id": "B",
        "part_type": "fastener",
        "quantity": 8,
        "volume": 50.0,
        "dimensions": {"width": 1, "height": 1, "depth": 5}
      }
    ],
    "total_parts": 2
  }
```

### 5. Assembly Steps

```
REQUEST:
  POST /api/v1/step/assembly-analysis
  Content-Type: application/json
  {
    "model_id": "550e8400-e29b-41d4-a716-446655440000"
  }
  ?preview_only=false

RESPONSE:
  {
    "model_id": "550e8400-e29b-41d4-a716-446655440000",
    "steps": [
      {
        "step_number": 1,
        "title": "Montaż boku lewego",
        "description": "Połącz bok lewy z dolną półką",
        "detail_description": "Wyrównaj krawędzie i wstrzyknij 4 konfirmaty...",
        "part_indices": [0, 5],
        "part_roles": {
          "0": "panel boczny",
          "5": "konfirmat"
        },
        "context_part_indices": [],
        "duration_minutes": 5,
        "assembly_sequence": ["Wyrównaj", "Wstaw konfirmaty", "Dokręć"],
        "warnings": ["Uważaj na krawędzie"],
        "tips": ["Użyj śruby metrycznej"],
        "confidence_score": 0.95,
        "is_llm_generated": true
      }
    ],
    "total_steps": 12
  }
```

## Frontend State Management

### Zustand Store Structure

```typescript
// Processing State
{
  jobId: "f47ac10b-...",           // Current upload job
  modelId: "550e8400-...",         // Current model
  status: "processing",             // idle | uploading | processing | complete | error
  progress: 45,                     // 0-100%
  currentStage: "loading_geometry", // Stage name
  errorMessage: null                // Error if any
}

// Model State
{
  geometry: {                        // 3D geometry
    vertices: [...],
    normals: [...],
    indices: [...]
  },
  parts: [...],                      // Extracted parts
  assembly: {...},                   // Assembly instructions
  isLoading: false,
  error: null
}

// Navigation
currentView: "upload" | "viewer" | "parts" | "assembly"
```

## Security & Performance

### Security
- File validation: Format + size checks
- API validation: Input sanitization
- CORS: Configured by deployment
- Type safety: Full TypeScript coverage

### Performance
- SSE: Low-latency progress updates
- Code splitting: Per-route bundles
- Lazy loading: On-demand components
- 3D optimization: Efficient rendering
- State management: Minimal re-renders

## Deployment Architecture

```
Internet
   ↓
Load Balancer (Optional)
   ↓
┌─────────────────────────────┐
│  Frontend (Next.js)         │  Port 3000
│  - Vercel / Docker / VPS    │
└─────────────────────────────┘
         ↓ HTTPS
┌─────────────────────────────┐
│  Backend (FastAPI)          │  Port 8000
│  - Docker / VPS / Cloud     │
└─────────────────────────────┘
         ↓
┌─────────────────────────────┐
│  Database (SQLite/PostgreSQL)
│  - File / Cloud Database    │
└─────────────────────────────┘
         ↓
┌─────────────────────────────┐
│  Storage (Optional)         │
│  - S3 / Local FS            │
└─────────────────────────────┘
```

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 16 | React framework |
| | React 19 | UI library |
| | TypeScript | Type safety |
| | Tailwind CSS | Styling |
| | Three.js | 3D graphics |
| | Zustand | State management |
| | Axios | HTTP client |
| **Backend** | FastAPI | Web framework |
| | Python 3.11+ | Language |
| | CadQuery | CAD processing |
| | Pydantic | Validation |
| | SQLAlchemy | Database ORM |
| | Alembic | Migrations |
| **Deployment** | Docker | Containerization |
| | Nginx | Reverse proxy |
| | PostgreSQL | Database (optional) |

---

**This diagram represents the complete WEBLE system architecture with full frontend implementation.**
