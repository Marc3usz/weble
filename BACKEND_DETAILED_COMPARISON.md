# WEBLE Backend - Detailed Endpoint Comparison & Data Flow

## Complete Endpoint Reference with Examples

### ENDPOINT 1: POST /api/v1/step/upload

#### Full Request Example
`
POST /api/v1/step/upload HTTP/1.1
Host: localhost:8000
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="assembly.step"
Content-Type: application/octet-stream

[BINARY STEP FILE CONTENT]
------WebKitFormBoundary--
`

#### Full Response Example
`
HTTP/1.1 200 OK
Content-Type: application/json

{
  "job_id": "a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6",
  "model_id": "f4a5b6c7-d8e9-40f1-a2b3-c4d5e6f7a8b9",
  "status": "processing",
  "estimated_time_seconds": 60
}
`

#### Implementation Details
File: backend/app/api/v1/endpoints/step.py (lines 33-100)
- Validates file size (max 50 MB)
- Validates STEP format (magic bytes: ISO-10303-21, min 100 bytes)
- Creates model record in database
- Creates job record with PROCESSING status
- Triggers ProcessingPipeline as background task
- Returns immediately (doesn't wait for processing)

#### Database Operations
Repository methods called:
- repository.create_model(model_id, file.filename, file_size)
- repository.create_job(job_id, model_id, ProcessingStatus.PROCESSING)

#### Error Scenarios

Error 1: Invalid file format
`
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "INVALID_STEP_FILE",
  "message": "File is not a valid STEP file or too small"
}
`

Error 2: File too large (>50MB)
`
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "FILE_TOO_LARGE",
  "message": "File size 60000000 exceeds max size 52428800 bytes"
}
`

Error 3: Missing file
`
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "error": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": [{"loc": ["body", "file"], "msg": "field required", ...}]
}
`

---

### ENDPOINT 2: GET /api/v1/step/progress/{job_id}/stream

#### Full Request Example
`
GET /api/v1/step/progress/a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6/stream HTTP/1.1
Host: localhost:8000
Accept: text/event-stream
`

#### Full Response Example (SSE Stream)
`
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no

data: {"job_id":"a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6","status":"processing","progress_percent":5,"current_stage":"loading_geometry","action":"Initializing STEP file parsing...","eta_seconds":60,"error_message":null,"timestamp":null}

data: {"job_id":"a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6","status":"processing","progress_percent":25,"current_stage":"loading_geometry","action":"Loaded 1024 vertices from STEP file","eta_seconds":45,"error_message":null,"timestamp":null}

data: {"job_id":"a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6","status":"processing","progress_percent":30,"current_stage":"extracting_parts","action":"Extracting and classifying parts...","eta_seconds":30,"error_message":null,"timestamp":null}

data: {"job_id":"a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6","status":"complete","progress_percent":50,"current_stage":"extracting_parts","action":"Extracted 15 parts, classified into categories","eta_seconds":20,"error_message":null,"timestamp":null}

data: {"job_id":"a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6","status":"processing","progress_percent":60,"current_stage":"generating_svgs","action":"Generating isometric technical drawings...","eta_seconds":20,"error_message":null,"timestamp":null}

data: {"job_id":"a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6","status":"complete","progress_percent":75,"current_stage":"generating_svgs","action":"Generated 15 SVG drawings","eta_seconds":10,"error_message":null,"timestamp":null}

data: {"job_id":"a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6","status":"processing","progress_percent":80,"current_stage":"generating_assembly","action":"Analyzing parts and generating assembly sequence...","eta_seconds":10,"error_message":null,"timestamp":null}

data: {"job_id":"a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6","status":"complete","progress_percent":95,"current_stage":"generating_assembly","action":"Generated 8 assembly steps","eta_seconds":2,"error_message":null,"timestamp":null}

data: {"job_id":"a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6","status":"success","progress_percent":100,"current_stage":"complete","action":"All processing stages completed successfully","eta_seconds":0,"error_message":null,"timestamp":null}
`

#### Implementation Details
File: backend/app/api/v1/endpoints/step.py (lines 262-335)
- Gets ProgressTracker from container
- Subscribes to job_id events
- Sends event history to new subscribers
- Transforms ProgressEvent to ProgressStreamResponse
- Field mapping: stage→current_stage, percentage→progress_percent, message→action
- Closes on "complete" or "failed" status

#### Event Structure
ProgressEvent (internal):
- stage: str
- status: str
- percentage: int
- message: str
- data: Dict[str, Any] (contains eta_seconds, error_message, timestamp)

ProgressStreamResponse (API):
- job_id: str
- status: str
- progress_percent: int
- current_stage: str
- action: str
- eta_seconds: int
- error_message: Optional[str]
- timestamp: Optional[str]

#### Processing Pipeline Stages

Stage 1: Loading Geometry (0-25%)
- Event 1: percentage=5, action="Initializing STEP file parsing..."
- Event 2: percentage=25, action="Loaded [N] vertices from STEP file"

Stage 2: Extracting Parts (25-50%)
- Event 1: percentage=30, action="Extracting and classifying parts..."
- Event 2: percentage=50, action="Extracted [N] parts, classified into categories"

Stage 3: Generating SVGs (50-75%)
- Event 1: percentage=60, action="Generating isometric technical drawings..."
- Event 2: percentage=75, action="Generated [N] SVG drawings"

Stage 4: Generating Assembly (75-100%)
- Event 1: percentage=80, action="Analyzing parts and generating assembly sequence..."
- Event 2: percentage=95, action="Generated [N] assembly steps"

Final: Completion (100%)
- Event: percentage=100, status="success", action="All processing stages completed successfully"

#### Error Stream Example
`
data: {"job_id":"a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6","status":"failed","progress_percent":0,"current_stage":"error","action":"Pipeline failed: No solids found in assembly","eta_seconds":0,"error_message":"No solids found in assembly","timestamp":null}
`

---

### ENDPOINT 3: GET /api/v1/jobs/{job_id}

#### Full Request Example
`
GET /api/v1/jobs/a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6 HTTP/1.1
Host: localhost:8000
Accept: application/json
`

#### Full Response Example (In Progress)
`
HTTP/1.1 200 OK
Content-Type: application/json

{
  "job_id": "a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6",
  "model_id": "f4a5b6c7-d8e9-40f1-a2b3-c4d5e6f7a8b9",
  "status": "processing",
  "progress_percent": 50,
  "current_stage": "extracting_parts",
  "action": "Extracted 15 parts",
  "eta_seconds": 20,
  "error_message": null
}
`

#### Full Response Example (Complete)
`
HTTP/1.1 200 OK
Content-Type: application/json

{
  "job_id": "a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6",
  "model_id": "f4a5b6c7-d8e9-40f1-a2b3-c4d5e6f7a8b9",
  "status": "complete",
  "progress_percent": 100,
  "current_stage": "complete",
  "action": "Pipeline completed successfully",
  "eta_seconds": 0,
  "error_message": null
}
`

#### Full Response Example (Failed)
`
HTTP/1.1 200 OK
Content-Type: application/json

{
  "job_id": "a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6",
  "model_id": "f4a5b6c7-d8e9-40f1-a2b3-c4d5e6f7a8b9",
  "status": "failed",
  "progress_percent": 0,
  "current_stage": "error",
  "action": "No solids found in assembly",
  "eta_seconds": 0,
  "error_message": "No solids found in assembly"
}
`

#### Response Schema
JobStatusResponse (BaseModel):
- job_id: str
- status: str
- progress_percent: int
- current_stage: str
- action: str = ""
- eta_seconds: int = 0
- error_message: Optional[str] = None

#### Implementation Details
File: backend/app/api/v1/endpoints/step.py (lines 338-367)
- Gets repository from container
- Calls repository.get_job(job_id)
- Maps ProcessingJob to JobStatusResponse
- Field mapping: job.status.value (enum to string)

---

### ENDPOINT 4: GET /api/v1/step/{model_id}

#### Full Request Example
`
GET /api/v1/step/f4a5b6c7-d8e9-40f1-a2b3-c4d5e6f7a8b9 HTTP/1.1
Host: localhost:8000
Accept: application/json
`

#### Full Response Example (With Geometry)
`
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "success",
  "model_id": "f4a5b6c7-d8e9-40f1-a2b3-c4d5e6f7a8b9",
  "file_name": "cabinet.step",
  "file_size": 245632,
  "geometry_loaded": true,
  "geometry": {
    "vertices": [
      [0.0, 0.0, 0.0],
      [100.0, 0.0, 0.0],
      [100.0, 80.0, 0.0],
      [0.0, 80.0, 0.0],
      [0.0, 0.0, 40.0],
      [100.0, 0.0, 40.0],
      [100.0, 80.0, 40.0],
      [0.0, 80.0, 40.0],
      [20.0, 20.0, 0.0],
      [80.0, 20.0, 0.0],
      [80.0, 60.0, 0.0],
      [20.0, 60.0, 0.0]
    ],
    "normals": [
      [0.0, 0.0, -1.0],
      [0.0, 0.0, 1.0],
      [0.0, -1.0, 0.0],
      [0.0, 1.0, 0.0],
      [-1.0, 0.0, 0.0],
      [1.0, 0.0, 0.0],
      [0.0, -0.707, 0.707],
      [0.707, 0.0, 0.707]
    ],
    "indices": [
      0, 1, 2, 0, 2, 3,
      4, 6, 5, 4, 7, 6,
      0, 4, 5, 0, 5, 1,
      1, 5, 6, 1, 6, 2,
      2, 6, 7, 2, 7, 3,
      3, 7, 4, 3, 4, 0,
      8, 9, 10, 8, 10, 11
    ],
    "metadata": {
      "solids": [
        {
          "bounding_box": {
            "min": [0.0, 0.0, 0.0],
            "max": [100.0, 80.0, 40.0]
          },
          "centroid": [50.0, 40.0, 20.0],
          "volume": 320000.0,
          "surface_area": 23600.0
        },
        {
          "bounding_box": {
            "min": [20.0, 20.0, 0.0],
            "max": [80.0, 60.0, 5.0]
          },
          "centroid": [50.0, 40.0, 2.5],
          "volume": 10000.0,
          "surface_area": 6600.0
        }
      ]
    }
  }
}
`

#### Response Example (No Geometry Yet)
`
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "success",
  "model_id": "f4a5b6c7-d8e9-40f1-a2b3-c4d5e6f7a8b9",
  "file_name": "assembly.step",
  "file_size": 123456,
  "geometry_loaded": false,
  "geometry": null
}
`

#### Response Example (Not Found)
`
HTTP/1.1 200 OK
Content-Type: application/json

{
  "error": "Model not found"
}
`

#### Geometry Structure Explained

Vertices (Triangle Mesh):
- Each vertex is [x, y, z] coordinate
- Typically thousands of vertices for complex models
- Measured in original CAD units (usually mm)

Normals (Surface Normals):
- Each normal is [nx, ny, nz] unit vector
- Used for lighting calculations in 3D viewer
- One normal per vertex or per face

Indices (Face Indices):
- Groups of 3 integers representing triangle faces
- Example: [0, 1, 2] = triangle using vertices 0, 1, 2
- Total indices length always multiple of 3

Metadata.Solids (Solid Objects):
- One entry per solid in the STEP file
- bounding_box.min: [x_min, y_min, z_min]
- bounding_box.max: [x_max, y_max, z_max]
- centroid: Center of mass [x, y, z]
- volume: In cubic units (cm³ typical)
- surface_area: In square units (cm² typical)

#### Implementation Details
File: backend/app/api/v1/endpoints/step.py (lines 103-138)
- Gets repository from container
- Calls repository.get_model(model_id)
- Calls repository.get_geometry(model_id)
- Returns wrapped geometry in response

---

### ENDPOINT 5: POST /api/v1/step/parts-2d

#### Full Request Example
`
POST /api/v1/step/parts-2d HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "model_id": "f4a5b6c7-d8e9-40f1-a2b3-c4d5e6f7a8b9"
}
`

#### Alternative Request (Accepts Both Field Names)
`
{
  "modelId": "f4a5b6c7-d8e9-40f1-a2b3-c4d5e6f7a8b9"
}
`

#### Full Response Example
`
HTTP/1.1 200 OK
Content-Type: application/json

{
  "model_id": "f4a5b6c7-d8e9-40f1-a2b3-c4d5e6f7a8b9",
  "parts": [
    {
      "id": "A",
      "part_type": "panel",
      "quantity": 2,
      "volume": 16000.0,
      "dimensions": {
        "width": 100.0,
        "height": 80.0,
        "depth": 2.0
      }
    },
    {
      "id": "B",
      "part_type": "structural",
      "quantity": 4,
      "volume": 8000.0,
      "dimensions": {
        "width": 100.0,
        "height": 2.0,
        "depth": 40.0
      }
    },
    {
      "id": "C",
      "part_type": "hardware",
      "quantity": 12,
      "volume": 5.0,
      "dimensions": {
        "width": 5.0,
        "height": 5.0,
        "depth": 0.2
      }
    },
    {
      "id": "D",
      "part_type": "fastener",
      "quantity": 24,
      "volume": 0.5,
      "dimensions": {
        "width": 3.0,
        "height": 3.0,
        "depth": 5.0
      }
    }
  ],
  "total_parts": 4
}
`

#### Part Classification Logic

Panel detection:
- width/height >> depth (width × height >> depth)
- Typical: 100×80×2 mm (large flat surface)
- Used for walls, shelves, panels

Structural detection:
- Balanced dimensions with high volume
- Typical: 100×40×2 mm beam/frame
- Used for support, frames, bracing

Hardware detection:
- Small, specific dimensions (bolts, washers)
- Typical: 5×5×0.2 mm
- Predefined component sizes

Fastener detection:
- Small volume, specific aspect ratio
- Typical: 3×3×5 mm (screw-like)
- Used for screws, rivets, pins

Other:
- Anything that doesn't match above patterns

#### Deduplication Process
Input solids from geometry metadata:
`
Solid 0: dims 100×80×2, volume 16000
Solid 1: dims 100×80×2, volume 16000  (duplicate of Solid 0)
Solid 2: dims 100×2×40, volume 8000
Solid 3: dims 100×2×40, volume 8000   (duplicate of Solid 2)
...
`

Adaptive tolerance calculation:
- Base tolerance: 15%
- Min: 5% (high precision)
- Max: 30% (loose matching)
- Adjusted based on model scale

After deduplication:
`
Part A: id="A", quantity=2 (solids 0,1)
Part B: id="B", quantity=2 (solids 2,3)
...
`

#### Implementation Details
File: backend/app/api/v1/endpoints/step.py (lines 141-195)
- Accepts model_id or modelId from request body
- Gets cached parts if available
- Otherwise: extract from geometry and cache
- Returns PartsResponse with part list

#### Error Scenarios

Error 1: Missing model_id
`
HTTP/1.1 400 Bad Request
Content-Type: application/json

{"detail": "modelId is required"}
`

Error 2: Model not found
`
HTTP/1.1 400 Bad Request
Content-Type: application/json

{"detail": "Model not found"}
`

Error 3: Geometry not available
`
HTTP/1.1 400 Bad Request
Content-Type: application/json

{"detail": "Model geometry is not available"}
`

---

### ENDPOINT 6: POST /api/v1/step/assembly-analysis

#### Full Request Example
`
POST /api/v1/step/assembly-analysis HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "model_id": "f4a5b6c7-d8e9-40f1-a2b3-c4d5e6f7a8b9"
}
`

#### Request with Preview Mode
`
POST /api/v1/step/assembly-analysis?preview_only=true HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "modelId": "f4a5b6c7-d8e9-40f1-a2b3-c4d5e6f7a8b9"
}
`

#### Full Response Example (LLM-Generated, Phase 3)
`
HTTP/1.1 200 OK
Content-Type: application/json

{
  "model_id": "f4a5b6c7-d8e9-40f1-a2b3-c4d5e6f7a8b9",
  "steps": [
    {
      "step_number": 1,
      "title": "Assemble the base frame",
      "description": "Connect the four structural supports using corner brackets and bolts",
      "detail_description": "Start by laying out the two longer structural pieces (Part B) parallel to each other, about 80mm apart. Take the two shorter structural pieces and position them perpendicular at each end, forming a rectangle. Ensure all corners are at 90 degrees using a carpenter's square or by checking diagonal measurements are equal. Attach corner brackets (Part C) at all four corners using M6 bolts and washers. Tighten bolts firmly but do not over-tighten.",
      "part_indices": [1, 1, 1, 1],
      "part_roles": {
        "1": "support_frame"
      },
      "context_part_indices": [2],
      "duration_minutes": 12,
      "assembly_sequence": [
        "Layout parallel pieces",
        "Position perpendicular pieces",
        "Square the corners",
        "Install corner brackets",
        "Tighten all bolts"
      ],
      "warnings": [
        "Ensure frame is square before tightening all bolts",
        "Do not over-tighten bolts - can damage wood",
        "Wear safety glasses when handling metal brackets"
      ],
      "tips": [
        "Use a speed square or carpenter's square to check angles",
        "Tighten bolts gradually in a cross pattern",
        "Pre-drill holes if working with wood to prevent splitting"
      ],
      "confidence_score": 0.94,
      "is_llm_generated": true
    },
    {
      "step_number": 2,
      "title": "Attach the panel layers",
      "description": "Install the side and top panels onto the frame",
      "detail_description": "Take the first side panel (Part A) and align its edge with the outer edge of the frame. It should sit flush against the frame pieces. Use the provided fasteners (Part D) to secure the panel at each corner and along the edges (spacing approximately 100mm apart). Ensure the panel is flush and square before driving in all fasteners completely. Repeat for the second side panel, ensuring both panels are perfectly vertical and flush with the frame. Finally, position the top panel and secure in the same manner.",
      "part_indices": [0, 0],
      "part_roles": {
        "0": "side_panel"
      },
      "context_part_indices": [1],
      "duration_minutes": 18,
      "assembly_sequence": [
        "Position first panel",
        "Align edges and ensure flush",
        "Secure with fasteners",
        "Verify vertical alignment",
        "Install second panel",
        "Attach top panel",
        "Final tightening"
      ],
      "warnings": [
        "Do not force panels - they should fit smoothly",
        "Tighten fasteners sequentially, not in one location",
        "Check that assembly remains square throughout"
      ],
      "tips": [
        "Use shims to ensure perfect alignment",
        "Pre-fill fastener holes to prevent splitting",
        "Have a helper to hold panels in position"
      ],
      "confidence_score": 0.91,
      "is_llm_generated": true
    },
    {
      "step_number": 3,
      "title": "Install hardware and final checks",
      "description": "Add corner reinforcements and perform quality checks",
      "detail_description": "Install the corner reinforcement hardware (Part C) at the top edges of the assembly where the side panels meet the top panel. This provides additional structural support. Use M5 bolts with washers and lock washers. After all fasteners are installed, perform a final inspection: check that all bolts are tight, panels are flush and square, and there are no visible gaps. Rock the assembly gently to ensure it is stable and does not flex excessively.",
      "part_indices": [2],
      "part_roles": {
        "2": "reinforcement"
      },
      "context_part_indices": [0, 1],
      "duration_minutes": 8,
      "assembly_sequence": [
        "Install reinforcements",
        "Tighten all hardware",
        "Check panel alignment",
        "Inspect for gaps",
        "Test stability"
      ],
      "warnings": [
        "Ensure lock washers are used on all bolts",
        "Do not skip quality inspection",
        "Assembly should not flex or wobble"
      ],
      "tips": [
        "Mark each bolt with paint as you tighten for tracking",
        "Use a torque wrench for consistent bolt tightness",
        "Have assembly on a level surface during inspection"
      ],
      "confidence_score": 0.88,
      "is_llm_generated": true
    }
  ],
  "total_steps": 3
}
`

#### Response Example (Rules-Based Fallback)
`
HTTP/1.1 200 OK
Content-Type: application/json

{
  "model_id": "f4a5b6c7-d8e9-40f1-a2b3-c4d5e6f7a8b9",
  "steps": [
    {
      "step_number": 1,
      "title": "Assemble part B",
      "description": "Connect structural elements",
      "detail_description": "",
      "part_indices": [1],
      "part_roles": {"1": "structural_component"},
      "context_part_indices": [],
      "duration_minutes": 5,
      "assembly_sequence": [],
      "warnings": [],
      "tips": [],
      "confidence_score": 0.8,
      "is_llm_generated": false
    },
    {
      "step_number": 2,
      "title": "Attach part A",
      "description": "Secure panels to the structure",
      "detail_description": "",
      "part_indices": [0],
      "part_roles": {"0": "panel"},
      "context_part_indices": [1],
      "duration_minutes": 8,
      "assembly_sequence": [],
      "warnings": [],
      "tips": [],
      "confidence_score": 0.8,
      "is_llm_generated": false
    }
  ],
  "total_steps": 2
}
`

#### Response Example (Preview Mode - Fast)
`
HTTP/1.1 200 OK
Content-Type: application/json

{
  "model_id": "f4a5b6c7-d8e9-40f1-a2b3-c4d5e6f7a8b9",
  "steps": [
    {
      "step_number": 1,
      "title": "Step 1",
      "description": "Quick assembly preview",
      "detail_description": "",
      "part_indices": [0, 1],
      "part_roles": {},
      "context_part_indices": [],
      "duration_minutes": 0,
      "assembly_sequence": [],
      "warnings": [],
      "tips": [],
      "confidence_score": 0.5,
      "is_llm_generated": false
    }
  ],
  "total_steps": 1
}
`

#### Phase 3 LLM Features Explained

detail_description:
- Expanded 2-3 sentence description
- Step-by-step sub-actions
- Specific measurements and alignments
- Safety considerations woven in
- Written in IKEA tone (cheerful, accessible)

assembly_sequence:
- List of sub-steps for the main step
- Example: ["Position", "Align", "Secure", "Tighten"]
- Helps users break down complex steps
- 3-7 items typical per step

warnings:
- Safety cautions
- Common mistakes to avoid
- Physical hazards
- Tools required
- Example: "Do not over-tighten bolts"

tips:
- Helpful hints for success
- Tools or techniques
- Pro tips from experience
- Example: "Use a carpenter's square to check angles"

confidence_score:
- 0.0-1.0 (higher = more confident)
- LLM-generated: typically 0.85-0.95
- Rules-based: typically 0.8 (default)
- Indicates quality of generation

is_llm_generated:
- true: Generated by LLM model
- false: Generated by rules-based system
- Lets frontend show quality indicators

#### Implementation Details
File: backend/app/api/v1/endpoints/step.py (lines 198-259)
- Accepts model_id or modelId
- Accepts preview_only query param
- Gets or generates parts (if needed)
- Gets or generates drawings (if needed)
- Calls AssemblyGeneratorService.process()
- Service chooses LLM or rules-based path
- Returns AssemblyResponse

---

## Data Flow Example: Complete Processing

### Request Flow
`
1. Client uploads STEP file
   POST /api/v1/step/upload (with file)
   ↓ Returns job_id, model_id, status="processing"

2. Client subscribes to progress
   GET /api/v1/step/progress/{job_id}/stream
   ↓ SSE stream starts

3. Background pipeline executes
   Stage 1: StepLoaderService.process(file_content) → Geometry3D
   Stage 2: PartsExtractorService.process(geometry) → Parts[]
   Stage 3: SvgGeneratorService.process(parts) → SvgDrawing[]
   Stage 4: AssemblyGeneratorService.process(parts, drawings) → AssemblyStep[]

4. Pipeline emits progress events
   Each stage emits ProgressEvent with percentage, stage, action
   ProgressTracker broadcasts to all subscribers

5. Client receives SSE events
   Each event contains: status, progress_percent, current_stage, action

6. On completion, client queries endpoints
   GET /api/v1/step/{model_id} → Geometry
   POST /api/v1/step/parts-2d → PartsResponse
   POST /api/v1/step/assembly-analysis → AssemblyResponse
`

### Database State Progression

`
Uploaded:
  models: {model_id: {file_name, file_size, geometry=null, metadata={}}}
  jobs: {job_id: {id, model_id, status="processing", progress=0, ...}}

After Stage 1:
  models: {model_id: {..., geometry=Geometry3D{vertices, normals, ...}}}
  jobs: {job_id: {..., status="processing", progress=25, ...}}

After Stage 2:
  parts: {model_id: [Part{id, type, quantity, ...}, ...]}
  jobs: {job_id: {..., status="processing", progress=50, ...}}

After Stage 3:
  drawings: {model_id: [SvgDrawing{part_id, svg_content, ...}, ...]}
  jobs: {job_id: {..., status="processing", progress=75, ...}}

After Stage 4:
  steps: {model_id: [AssemblyStep{step_number, title, ...}, ...]}
  jobs: {job_id: {..., status="complete", progress=100, ...}}
`

---

Document Version: 2.0
Last Updated: April 19, 2026
Focus: Detailed endpoint examples and data flow
