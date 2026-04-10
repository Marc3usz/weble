# WEBLE Pipeline Architecture: Research & Design Patterns

**Document Purpose**: Comprehensive guide for understanding multi-stage CAD processing pipelines, data transformations, optimal library choices, and architecture patterns for the WEBLE system (STEP → Geometry → Parts → Assembly).

**Last Updated**: April 2026

---

## 1. WEBLE Pipeline: Key Data Transformations

### 1.1 Overview

The WEBLE pipeline is a **4-stage sequential transformation system**:

```
STEP File → 3D Geometry → Parts Extraction → Assembly Instructions
   (Raw)      (Processed)     (Classified)       (Structured)
```

Each stage accepts input from the previous stage, applies transformations, and passes structured output to the next stage. Understanding what each stage must communicate is critical for robust architecture.

### 1.2 Stage 1: STEP File Upload & 3D Geometry Extraction

**Input**:
- Raw STEP/STP file (binary format, ASCII variant also possible)
- File metadata (name, size, upload timestamp)

**Transformations**:
1. Parse binary/ASCII STEP structure into CAD model representation
2. Extract topology: solids, shells, faces, edges, vertices
3. Generate 3D geometry:
   - Vertices (XYZ coordinates)
   - Face normals (for lighting)
   - Triangulation (for mesh rendering)
4. Calculate bounding box (for viewport fitting)
5. Build face adjacency graph (for part separation later)

**Output Data Structure**:
```json
{
  "modelId": "uuid",
  "fileHash": "sha256",
  "boundingBox": {
    "min": {"x": 0, "y": 0, "z": 0},
    "max": {"x": 100, "y": 200, "z": 150}
  },
  "geometry": {
    "vertices": [0.0, 1.5, 2.3, ...],  // Flattened array
    "normals": [0.0, 1.0, 0.0, ...],
    "indices": [0, 1, 2, ...]
  },
  "solids": [
    {
      "solidId": "solid_0",
      "shellCount": 1,
      "faceCount": 12,
      "vertices": 36,
      "volume": 1234.56,
      "centroid": {"x": 50, "y": 100, "z": 75}
    }
  ],
  "metadata": {
    "triangulationQuality": "medium",  // or "high", "low"
    "processingTimeMs": 2500,
    "textureCoordinates": false
  }
}
```

**Key Design Decisions**:
- **Flattened arrays** for geometry: More efficient for WebGL/Three.js than nested structures
- **Per-solid metadata**: Enables independent processing and caching
- **Centroid calculation**: Critical for part grouping later (see Stage 2)
- **Face adjacency tracking** (internal): Needed for splitting solids into parts

**Critical Data for Next Stage**:
- Solid IDs and their geometry
- Centroid + volume (for similarity matching)
- Face topology (which faces are adjacent)

---

### 1.3 Stage 2: Parts Extraction & Classification

**Input**:
- Geometry data from Stage 1
- Solids with topology information
- Tolerance parameters (default 15% for dimensions/volume)

**Transformations**:
1. **Part Extraction**: If a solid contains multiple disconnected components, split it
   - Use face adjacency graph and flood-fill algorithm
   - Each connected component = separate part
2. **Part Deduplication**: Identify identical/similar parts
   - Calculate volume, bounding box dimensions, principal axes
   - Use tolerance-based comparison (±15%)
   - Group similar parts together
3. **Part Classification**:
   - **Panels**: Bounding box aspect ratio indicates flatness (e.g., 100×200×2)
   - **Hardware**: Small volume, metallic properties (if available)
   - **Fasteners**: Specific geometric signatures (screws, dowels, cam locks)
   - **Structural**: Medium/large, not flat
4. **2D Drawing Generation**:
   - Isometric projection or orthographic view
   - Hidden line removal (HLR) for technical accuracy
   - Generate SVG for each unique part
5. **Quantity Notation**:
   - For groups of identical parts (e.g., 12×M4 screws), create single drawing with ×12 label

**Output Data Structure**:
```json
{
  "modelId": "uuid",
  "parts": [
    {
      "partId": "part_A_001",
      "solidIds": ["solid_0"],  // May contain multiple solids if grouped
      "quantity": 1,
      "classification": "panel",
      "metrics": {
        "volume": 1234.56,
        "boundingBox": {"width": 100, "height": 200, "depth": 2},
        "principalAxes": [[1,0,0], [0,1,0], [0,0,1]],
        "centroid": {"x": 50, "y": 100, "z": 1}
      },
      "svgDrawing": "<svg>...</svg>",
      "drawingType": "isometric",
      "material": "wood",  // If detectable
      "edges": [
        {
          "type": "straight",
          "length": 100,
          "orientation": "horizontal"
        }
      ]
    },
    {
      "partId": "part_B_001",
      "solidIds": ["solid_1", "solid_2", "solid_3"],  // 3 screws grouped
      "quantity": 3,
      "classification": "hardware",
      "metrics": { /* similar structure */ },
      "svgDrawing": "<svg>...</svg>",
      "deduplicationGroup": "fastener_type_1"
    }
  ],
  "partGroups": [
    {
      "groupId": "group_1",
      "parts": ["part_B_001", "part_C_001", "part_D_001"],
      "rationale": "All M4 wood screws, within 15% volume tolerance"
    }
  ],
  "processingMetadata": {
    "splitOperations": 2,
    "deduplicatedPairs": 15,
    "svgGenerationTimeMs": 3200
  }
}
```

**Key Design Decisions**:
- **Tolerance-based matching (15%)**: Balances false positives vs. true positives
  - 5% too strict (may miss variants)
  - 25% too loose (may group different parts)
- **Part ID naming**: `part_<letter>_<instance>` enables human-readable references (used in assembly steps)
- **Deduplication groups**: Crucial for assembly instruction logic (e.g., "add 12 screws of type X")
- **SVG generation once per unique part**: Expensive operation; caching is essential

**Critical Data for Next Stage**:
- Part IDs and classifications
- Quantities and deduplication groups
- Part metrics (for spatial relationship understanding)
- SVG drawings (for assembly step visualization)

---

### 1.4 Stage 3: Assembly Instruction Generation

**Input**:
- Parts data from Stage 2
- Part classifications and quantities
- SVG drawings and geometry

**Transformations**:
1. **Spatial Analysis**:
   - Determine part connectivity (which parts touch/overlap)
   - Identify main structure vs. fastening components
   - Build assembly dependency graph
2. **Logical Sequencing**:
   - Use AI (LLM) to analyze spatial relationships
   - Generate assembly order that:
     - Starts with base structure
     - Groups related assembly tasks
     - Minimizes tool changes
     - Considers ergonomics (access, orientation)
3. **Step Generation**:
   - For each assembly step:
     - Determine which parts are active (being connected)
     - Identify context parts (already assembled, shown as reference)
     - Generate descriptive text
     - Create exploded view SVG
4. **Cross-referencing**:
   - Link each step to specific part IDs
   - Assign roles (e.g., "side panel", "dowel connector")

**Output Data Structure**:
```json
{
  "modelId": "uuid",
  "assemblySteps": [
    {
      "stepNumber": 1,
      "title": "Assemble base frame",
      "description": "Connect left side panel (A) to bottom shelf (B) using 4 dowels. Ensure corners are square.",
      "partIndices": [0, 5],  // 0=left panel, 5=dowel connector
      "partRoles": {
        "0": "side panel",
        "5": "dowel connector"
      },
      "contextPartIndices": [],  // No context parts for step 1
      "explodedViewSvg": "<svg>...</svg>",
      "estimatedTimeMinutes": 5,
      "difficulty": "easy",
      "tools": ["mallet"]
    },
    {
      "stepNumber": 2,
      "title": "Attach back panel",
      "description": "Slide back panel (C) into grooves on side panels. Ensure it's flush.",
      "partIndices": [2],  // 2=back panel
      "partRoles": {
        "2": "back panel"
      },
      "contextPartIndices": [0, 5],  // Show previously assembled parts as reference
      "explodedViewSvg": "<svg>...</svg>",
      "estimatedTimeMinutes": 3,
      "difficulty": "easy",
      "tools": []
    },
    {
      "stepNumber": 3,
      "title": "Fasten with screws",
      "description": "Drive 12 screws through back panel into side panels. Use 3 screws per corner and 6 along edges.",
      "partIndices": [7],  // 7=M4 wood screws (quantity 12)
      "partRoles": {
        "7": "fastener"
      },
      "contextPartIndices": [0, 2, 5],
      "explodedViewSvg": "<svg>...</svg>",
      "estimatedTimeMinutes": 10,
      "difficulty": "moderate",
      "tools": ["drill", "screwdriver"]
    }
  ],
  "assemblyMetadata": {
    "totalEstimatedTimeMinutes": 45,
    "totalSteps": 8,
    "difficulty": "moderate",
    "toolsRequired": ["mallet", "drill", "screwdriver", "level"],
    "skillLevel": "intermediate"
  }
}
```

**Key Design Decisions**:
- **Exploded view SVGs**: One per step; shows before + after state
- **Context parts**: Enable users to understand spatial relationships
- **LLM-based sequencing**: Requires structured prompting; see Section 4.3
- **Estimated times**: Should be calibrated against user feedback
- **Tool tracking**: Helps users prepare and organize workspace

**Critical Data for Next Stage (Rendering)**:
- Assembly steps in sequence order
- Part references (must be resolvable to Part IDs from Stage 2)
- SVG diagrams (ready to display)
- Metadata for UI layout

---

### 1.5 Stage 4: Rendering & User Interaction (Frontend)

**Input**:
- Assembly steps from Stage 3
- Part data from Stage 2 (for quick reference)
- Geometry from Stage 1 (for 3D visualization)

**Transformations**:
1. **Step Viewer State Management**:
   - Track current step number
   - Highlight active parts
   - Fade/show context parts
2. **3D Animation**:
   - Explode/collapse animations between steps
   - Part highlighting and rotation
3. **2D Diagram Display**:
   - Render SVG diagrams at appropriate scale
   - Overlay dimension annotations
4. **Navigation**:
   - Next/Previous step controls
   - Step jump (click step in list)

**Output**: Interactive user interface

---

## 2. Python CAD Processing Libraries: Comparison

### 2.1 Overview Table

| Library | Backend | Speed | Ease | Python Quality | Cost | Best For |
|---------|---------|-------|------|---|------|----------|
| **CadQuery** | OpenCASCADE | Fast | High | Excellent | Free | STEP parsing, boolean ops, 2D projection |
| **Open3D** | Custom C++ | Very Fast | High | Good | Free | Point cloud, mesh processing |
| **Trimesh** | Custom C++ | Fast | Very High | Excellent | Free | Triangle mesh operations, analysis |
| **PyOCP** | OpenCASCADE | Fast | Medium | Good | Free | Direct OCP access (low-level) |
| **OCP (python-ocp)** | OpenCASCADE | Fast | Low | Poor | Free | Bare bindings, no convenience |
| **Parasolid** | Siemens Parasolid | Fastest | Medium | Good | Commercial | Enterprise CAD, maximum compatibility |
| **ACIS** | Autodesk ACIS | Fastest | Medium | Fair | Commercial | Enterprise, very stable |
| **Assimp** | Custom | Medium | High | Good | Free | Multi-format import, no CAD-specific ops |
| **Salome** | Multiple | Variable | Low | Fair | Free | Parametric, FEA integration (overkill for this) |
| **pyvista** | VTK | Fast | High | Good | Free | 3D visualization, mesh analysis |

### 2.2 Detailed Analysis

#### **CadQuery** ⭐ (Recommended for WEBLE)

**Strengths**:
- ✅ Excellent Python API wrapping OpenCASCADE (OCCT)
- ✅ Built-in STEP file parsing and writing
- ✅ Boolean operations (union, difference, intersection)
- ✅ Part extraction and solid manipulation
- ✅ Workplane concept enables intuitive part design
- ✅ Active community, good documentation
- ✅ Free and open-source
- ✅ Cross-platform (Windows, macOS, Linux)

**Weaknesses**:
- ⚠️ OpenCASCADE dependency adds build complexity
- ⚠️ Steeper learning curve than Trimesh (but worth it for CAD)
- ⚠️ Limited built-in visualization (must export to Three.js)
- ⚠️ Performance degrades with very large assemblies (>10,000 parts)

**WEBLE Usage**:
```python
import cadquery as cq

# Load STEP file
doc = cq.importers.importStep("assembly.step")

# Iterate solids
for solid in doc.solids():
    volume = solid.volume
    bbox = solid.BoundingBox()
    
# Export triangulated mesh
result = doc.val()
mesh = result.toMesh()  # Returns triangle data
```

**When to Use**: STEP parsing, part extraction, boolean operations, topology analysis.

---

#### **Trimesh** ⭐ (Complementary to CadQuery)

**Strengths**:
- ✅ Simplest API for triangle mesh operations
- ✅ Excellent for mesh cleaning, decimation, simplification
- ✅ Fast voxelization and convex hull operations
- ✅ Built-in support for many mesh formats (STL, OBJ, PLY, etc.)
- ✅ Cross-section generation (valuable for 2D drawings)
- ✅ Great documentation and examples
- ✅ Active development

**Weaknesses**:
- ⚠️ Works only with triangle meshes, not solids
- ⚠️ Cannot parse or manipulate STEP files directly
- ⚠️ Limited parametric/CAD-specific operations

**WEBLE Usage**:
```python
import trimesh

# Convert CadQuery solid to mesh
cq_mesh_data = cq_result.toMesh()
mesh = trimesh.Trimesh(
    vertices=cq_mesh_data['vertices'],
    faces=cq_mesh_data['faces']
)

# Simplification
simplified = mesh.simplify_mesh()

# Cross-sections
section = mesh.section_plane(
    plane_origin=[0, 0, 50],
    plane_normal=[0, 0, 1]
)
```

**When to Use**: Mesh optimization, cross-sections, convex hulls, bounding boxes, mesh analysis.

---

#### **Open3D** (Advanced mesh operations)

**Strengths**:
- ✅ Extremely fast C++ backend
- ✅ Point cloud and mesh processing
- ✅ Surface reconstruction (for noisy data)
- ✅ Registration and alignment algorithms
- ✅ Voxel grid operations

**Weaknesses**:
- ⚠️ Optimized for point clouds, less for pure meshes
- ⚠️ Less intuitive API than Trimesh
- ⚠️ Smaller community for CAD applications

**WEBLE Usage**: Less critical path, but useful for advanced mesh analysis if needed.

---

### 2.3 Recommended Stack for WEBLE

```
┌─────────────────────────────────────────────────┐
│  STEP File Input                                │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│  CadQuery                                       │
│  - Parse STEP                                   │
│  - Extract solids                               │
│  - Calculate topology & metrics                 │
│  - Generate triangulated mesh                   │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│  Trimesh (optional optimization)                │
│  - Mesh decimation if needed                    │
│  - Convex hull analysis                         │
│  - Part similarity detection                    │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│  HLR (Hidden Line Removal) - OpenCASCADE       │
│  - Generate 2D SVG technical drawings           │
│  - Isometric projections                        │
│  - Part cross-sections                          │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│  Three.js (Frontend)                            │
│  - 3D visualization                             │
│  - Interactive rendering                        │
└─────────────────────────────────────────────────┘
```

**Why this stack**:
1. CadQuery handles CAD-specific operations
2. Trimesh provides mesh optimization and analysis
3. OpenCASCADE HLR generates professional 2D drawings
4. Three.js renders in browser without server-side GPU

---

## 3. Design Patterns for Multi-Stage Processing Pipelines

### 3.1 Pipeline Pattern (Core Architecture)

**Definition**: A pipeline is a sequence of processing stages where each stage:
- Accepts input from the previous stage
- Performs independent transformations
- Passes output to the next stage
- Can be implemented asynchronously

**WEBLE Pipeline Architecture**:

```python
class Pipeline:
    """Generic multi-stage processing pipeline."""
    
    def __init__(self):
        self.stages = []
    
    def add_stage(self, stage: ProcessingStage):
        """Register a processing stage."""
        self.stages.append(stage)
    
    async def execute(self, input_data: InputData) -> OutputData:
        """Execute pipeline sequentially."""
        current = input_data
        
        for stage in self.stages:
            try:
                current = await stage.process(current)
                await self._emit_progress(stage.name, current)
            except Exception as e:
                await self._handle_error(stage.name, e)
                raise PipelineException(stage.name, e)
        
        return current

class ProcessingStage(ABC):
    """Abstract base for pipeline stages."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    async def process(self, data: Any) -> Any:
        pass
    
    @abstractmethod
    def validate_input(self, data: Any) -> bool:
        pass
    
    @abstractmethod
    def validate_output(self, data: Any) -> bool:
        pass
```

**Benefits**:
- ✅ Clear separation of concerns
- ✅ Easy to test each stage independently
- ✅ Easy to add/remove/reorder stages
- ✅ Supports both sync and async execution

---

### 3.2 Stage-Based Architecture

Each stage should be independently:
- **Testable**: Unit tests without other stages
- **Reusable**: Can be invoked from multiple contexts
- **Cacheable**: Results can be stored and reused
- **Monitorable**: Progress and error tracking

**WEBLE Stages**:

```python
# Stage 1: STEP File Loading
class StepFileLoadingStage(ProcessingStage):
    name = "step_loading"
    
    async def process(self, file_data: UploadedFile) -> RawGeometry:
        """
        Input: Binary STEP file
        Output: RawGeometry with solids, topology
        """
        # Implementation
        pass

# Stage 2: Parts Extraction
class PartsExtractionStage(ProcessingStage):
    name = "parts_extraction"
    
    async def process(self, geometry: RawGeometry) -> PartsList:
        """
        Input: RawGeometry from Stage 1
        Output: PartsList with classifications
        """
        # Implementation
        pass

# Stage 3: 2D Drawing Generation
class TwoDDrawingStage(ProcessingStage):
    name = "2d_drawing_generation"
    
    async def process(self, parts: PartsList) -> PartsWithDrawings:
        """
        Input: PartsList from Stage 2
        Output: PartsWithDrawings (adds SVG to each part)
        """
        # Implementation
        pass

# Stage 4: Assembly Analysis
class AssemblyAnalysisStage(ProcessingStage):
    name = "assembly_analysis"
    
    async def process(self, parts: PartsWithDrawings) -> AssemblySteps:
        """
        Input: PartsWithDrawings from Stage 3
        Output: AssemblySteps (ordered, with instructions)
        """
        # Implementation
        pass
```

---

### 3.3 Error Handling & Recovery Patterns

#### **Retry with Exponential Backoff**

For transient failures (API timeouts, temporary resource issues):

```python
class RetryableStage(ProcessingStage):
    """Stage that retries on failure."""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
    
    async def process(self, data: Any) -> Any:
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await self._do_process(data)
            except TransientError as e:
                last_exception = e
                wait_time = self.backoff_factor ** attempt
                await asyncio.sleep(wait_time)
                continue
        
        raise PipelineException(
            f"Failed after {self.max_retries} attempts",
            last_exception
        )
```

#### **Circuit Breaker**

For external services (LLM API, storage):

```python
class CircuitBreakerStage(ProcessingStage):
    """Prevents cascading failures by failing fast."""
    
    def __init__(self, failure_threshold: int = 5):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.state = "closed"  # or "open", "half_open"
    
    async def process(self, data: Any) -> Any:
        if self.state == "open":
            raise CircuitOpenException("Service temporarily unavailable")
        
        try:
            result = await self._do_process(data)
            self.failure_count = 0  # Reset on success
            self.state = "closed"
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise
```

#### **Checkpointing for Long Pipelines**

Save intermediate results to enable resumption:

```python
class CheckpointedPipeline(Pipeline):
    """Pipeline with checkpointing support."""
    
    def __init__(self, checkpoint_dir: Path):
        super().__init__()
        self.checkpoint_dir = checkpoint_dir
    
    async def execute(self, input_data: InputData, job_id: str) -> OutputData:
        current = input_data
        
        for i, stage in enumerate(self.stages):
            checkpoint_file = self.checkpoint_dir / f"{job_id}_stage_{i}.pkl"
            
            # Check if this stage already completed
            if checkpoint_file.exists():
                current = pickle.load(open(checkpoint_file, 'rb'))
                continue
            
            # Process stage
            current = await stage.process(current)
            
            # Save checkpoint
            pickle.dump(current, open(checkpoint_file, 'wb'))
        
        return current
```

---

### 3.4 Caching & Deduplication

**Why caching matters for CAD pipelines**:
- Part drawing generation (SVG from geometry) is expensive (~1-2s per part)
- Multiple parts may be identical or similar
- Same STEP file may be processed multiple times

```python
class CachedStage(ProcessingStage):
    """Stage with intelligent caching."""
    
    def __init__(self, cache_backend: CacheBackend = MemoryCache()):
        self.cache = cache_backend
    
    async def process(self, data: Any) -> Any:
        # Create cache key from input
        cache_key = self._compute_hash(data)
        
        # Check cache
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Process and cache
        result = await self._do_process(data)
        await self.cache.set(cache_key, result, ttl=3600)
        
        return result
    
    def _compute_hash(self, data: Any) -> str:
        """Hash input to create cache key."""
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
```

**Cache backends**:
- **Memory**: Fast, but lost on restart
- **Redis**: Fast, persistent across processes
- **Disk**: Slower, but persistent and surveyable
- **Hybrid**: Memory for hot data, disk for archive

---

### 3.5 Progress Tracking & User Feedback

**Server-Sent Events (SSE) Pattern**:

```python
class ProgressTrackingPipeline(Pipeline):
    """Pipeline that emits progress events."""
    
    def __init__(self):
        super().__init__()
        self.event_broadcaster = EventBroadcaster()
    
    async def execute(self, input_data: InputData, job_id: str) -> OutputData:
        current = input_data
        
        for i, stage in enumerate(self.stages):
            await self.event_broadcaster.broadcast(
                ProgressEvent(
                    job_id=job_id,
                    stage_name=stage.name,
                    progress=i / len(self.stages),
                    status="running"
                )
            )
            
            try:
                current = await stage.process(current)
                
                await self.event_broadcaster.broadcast(
                    ProgressEvent(
                        job_id=job_id,
                        stage_name=stage.name,
                        progress=(i + 1) / len(self.stages),
                        status="completed"
                    )
                )
            except Exception as e:
                await self.event_broadcaster.broadcast(
                    ProgressEvent(
                        job_id=job_id,
                        stage_name=stage.name,
                        status="failed",
                        error=str(e)
                    )
                )
                raise
        
        return current
```

**Frontend implementation** (React with TypeScript):

```typescript
useEffect(() => {
  const eventSource = new EventSource(`/api/jobs/${jobId}/progress`);
  
  eventSource.onmessage = (event) => {
    const progress = JSON.parse(event.data);
    setCurrentStage(progress.stage_name);
    setProgressPercent(progress.progress * 100);
  };
  
  eventSource.onerror = () => {
    setError("Connection lost");
    eventSource.close();
  };
  
  return () => eventSource.close();
}, [jobId]);
```

---

## 4. Real-World CAD/Assembly Systems: Production Patterns

### 4.1 Error Handling Strategy

**Categorize Errors**:

| Error Type | Cause | Recovery | User Message |
|-----------|-------|----------|--------------|
| **Invalid Input** | Corrupted STEP file | Reject, ask user to re-upload | "File appears corrupted" |
| **Geometry Error** | Degenerate faces, self-intersections | Attempt repair, or skip problematic parts | "Some parts may be simplified" |
| **Processing Timeout** | Large assembly (>100k parts) | Implement staged processing | "Large file - processing may take 2 mins" |
| **Transient Service** | LLM API temporarily down | Retry with backoff | "Generating instructions... retrying" |
| **Out of Memory** | Too large mesh for server | Downsample geometry | "Simplifying geometry for processing" |
| **Persistent Service** | LLM API permanently down | Skip step, provide manual template | "Assembly steps unavailable - see template" |

**Implementation**:

```python
class ErrorRecoveryHandler:
    """Handles different error types with appropriate recovery."""
    
    async def handle_error(self, error: Exception, context: ProcessingContext):
        if isinstance(error, InvalidStepFile):
            raise UserInputException(
                "File appears corrupted or invalid",
                suggestions=["Try re-exporting from CAD tool"]
            )
        
        elif isinstance(error, GeometryError):
            context.degraded_mode = True
            # Continue with problematic parts removed
            return context
        
        elif isinstance(error, TimeoutError):
            # For large files, trigger streaming/batching
            context.enable_streaming = True
            return context
        
        elif isinstance(error, ServiceUnavailableError):
            # Retry with exponential backoff
            await self._retry_with_backoff(context, max_retries=3)
        
        elif isinstance(error, OutOfMemoryError):
            # Downsample and retry
            context.downsample_geometry(factor=0.5)
            return context
        
        else:
            # Unknown error - log and fail
            logger.exception("Unexpected error", extra={"context": context})
            raise
```

---

### 4.2 Progress Tracking in Production

**Multi-layer tracking**:

```python
class DetailedProgressTracker:
    """Tracks progress at multiple levels of granularity."""
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.start_time = time.time()
        
        # Overall pipeline progress
        self.overall_progress = 0.0
        
        # Per-stage metrics
        self.stage_metrics = {}
        
        # Sub-stage detailed metrics (e.g., parts extracted so far)
        self.detail_metrics = {}
    
    async def update_stage(self, stage_name: str, progress: float, detail: str = None):
        """Update progress for current stage."""
        self.stage_metrics[stage_name] = {
            "progress": progress,
            "updated_at": time.time(),
            "elapsed_seconds": time.time() - self.start_time
        }
        
        if detail:
            self.detail_metrics[stage_name] = detail
        
        # Broadcast to frontend
        await self.broadcast({
            "stage": stage_name,
            "progress": progress,
            "detail": detail,
            "elapsed_seconds": int(time.time() - self.start_time)
        })
    
    def estimate_remaining_time(self, stage_name: str, current_progress: float) -> int:
        """Estimate remaining time based on historical data."""
        if current_progress == 0:
            return 0
        
        elapsed = time.time() - self.start_time
        estimated_total = elapsed / current_progress
        return int(estimated_total - elapsed)
```

---

### 4.3 LLM Integration for Assembly Instruction Generation

**Structured Prompting Pattern**:

```python
class AssemblyInstructionGenerator:
    """Generates assembly instructions via LLM with structured output."""
    
    async def generate(self, parts: PartsList, parts_with_drawings: PartsWithDrawings) -> AssemblySteps:
        """
        Generate assembly steps by:
        1. Creating structured prompt with part metadata
        2. Calling LLM API
        3. Parsing structured response
        4. Validating against parts list
        """
        
        # Step 1: Build detailed prompt
        prompt = self._build_prompt(parts, parts_with_drawings)
        
        # Step 2: Call LLM (with retry logic)
        response = await self._call_llm(prompt, model="gpt-4-turbo")
        
        # Step 3: Parse response
        steps = self._parse_response(response)
        
        # Step 4: Validate
        self._validate_steps(steps, parts)
        
        return steps
    
    def _build_prompt(self, parts: PartsList, drawings: PartsWithDrawings) -> str:
        """Build structured prompt for LLM."""
        
        # Include:
        # - Part names and quantities
        # - Part classifications (panel, hardware, etc.)
        # - Spatial relationships (which parts connect)
        # - Constraints (orientation, access requirements)
        
        return f"""
You are an expert furniture assembly instruction generator.

FURNITURE DESCRIPTION:
{self._describe_furniture(parts)}

PARTS LIST:
{self._format_parts_list(parts)}

SPATIAL RELATIONSHIPS:
{self._analyze_spatial_relationships(parts)}

CONSTRAINTS:
- Parts must be assembled in logical order (base first)
- Minimize tool changes
- Group related assembly tasks
- Consider accessibility (can assembler reach all parts?)

REQUIRED OUTPUT FORMAT (JSON):
{{
  "steps": [
    {{
      "stepNumber": 1,
      "title": "String describing main action",
      "description": "Detailed instructions, 1-2 sentences",
      "partIndices": [0, 1, 5],  // Indices into parts list
      "partRoles": {{"0": "side panel", "1": "dowel", "5": "fastener"}},
      "contextPartIndices": [],  // Parts already assembled, shown for reference
      "tools": ["mallet", "screwdriver"],
      "estimatedTimeMinutes": 5,
      "difficulty": "easy|moderate|hard"
    }}
  ]
}}

Generate clear, professional assembly instructions suitable for IKEA-style manuals.
"""
    
    async def _call_llm(self, prompt: str, model: str = "gpt-4-turbo", max_retries: int = 3) -> str:
        """Call LLM API with retry logic."""
        
        for attempt in range(max_retries):
            try:
                response = await self.client.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,  # Low temp for consistency
                    max_tokens=4000,
                    timeout=30
                )
                return response.choices[0].message.content
            
            except (TimeoutError, RateLimitError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    await asyncio.sleep(wait_time)
                else:
                    raise
    
    def _parse_response(self, response: str) -> AssemblySteps:
        """Extract JSON from LLM response."""
        
        try:
            # LLM might wrap JSON in markdown code blocks
            json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response
            
            data = json.loads(json_str)
            return AssemblySteps.from_dict(data)
        
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise LLMResponseParsingError(f"Invalid JSON in response: {response}")
    
    def _validate_steps(self, steps: AssemblySteps, parts: PartsList):
        """Validate that all referenced parts exist."""
        
        valid_indices = set(range(len(parts)))
        
        for step in steps.steps:
            # Check part indices
            for idx in step.partIndices:
                if idx not in valid_indices:
                    raise ValidationError(f"Step {step.stepNumber}: Invalid part index {idx}")
            
            for idx in step.contextPartIndices:
                if idx not in valid_indices:
                    raise ValidationError(f"Step {step.stepNumber}: Invalid context index {idx}")
            
            # Check that active parts != context parts
            active = set(step.partIndices)
            context = set(step.contextPartIndices)
            if active & context:
                logger.warning(f"Step {step.stepNumber}: Overlap between active and context parts")
```

---

### 4.4 Handling Large Assemblies (10,000+ Parts)

**Streaming & Batching Strategy**:

```python
class LargeAssemblyHandler:
    """Handles processing of large assemblies using streaming and batching."""
    
    async def process_large_assembly(self, geometry: RawGeometry, batch_size: int = 500):
        """
        Process large assemblies by:
        1. Batching part extraction
        2. Streaming results back to frontend
        3. Incremental classification and deduplication
        """
        
        all_parts = []
        
        # Extract parts in batches
        solids = geometry.solids
        for batch_start in range(0, len(solids), batch_size):
            batch_end = min(batch_start + batch_size, len(solids))
            batch = solids[batch_start:batch_end]
            
            # Process batch
            batch_parts = await self._process_part_batch(batch)
            all_parts.extend(batch_parts)
            
            # Emit progress
            progress = batch_end / len(solids)
            await self._emit_progress(f"Extracted {batch_end}/{len(solids)} parts", progress)
        
        # Deduplication phase (may also be batched)
        deduplicated = await self._deduplicate_parts(all_parts)
        
        return deduplicated
    
    async def _process_part_batch(self, solids: List[Solid]) -> List[Part]:
        """Process a batch of solids concurrently."""
        tasks = [self._process_single_part(s) for s in solids]
        return await asyncio.gather(*tasks)
    
    async def _process_single_part(self, solid: Solid) -> Part:
        """Process individual part (can be parallelized)."""
        # Extract geometry, calculate metrics, generate SVG
        pass
    
    async def _deduplicate_parts(self, parts: List[Part]) -> List[Part]:
        """
        Deduplicate using space-partitioning for efficiency.
        For 1000+ parts, naive O(n²) comparison is too slow.
        """
        
        # Group by volume range (fast first pass)
        volume_groups = self._group_by_volume_range(parts)
        
        # Within each volume group, compare carefully
        deduplicated = []
        for group in volume_groups:
            unique_in_group = self._deduplicate_group(group)
            deduplicated.extend(unique_in_group)
        
        return deduplicated
    
    def _group_by_volume_range(self, parts: List[Part], bucket_width: float = 100):
        """Group parts by volume range for efficient comparison."""
        groups = defaultdict(list)
        for part in parts:
            bucket = int(part.volume / bucket_width)
            groups[bucket].append(part)
        return list(groups.values())
    
    def _deduplicate_group(self, parts: List[Part], tolerance: float = 0.15) -> List[Part]:
        """Deduplicate within a group using iterative comparison."""
        # Start with first part as "unique"
        unique_parts = []
        
        for part in parts:
            is_duplicate = False
            
            for unique_part in unique_parts:
                if self._are_similar(part, unique_part, tolerance):
                    # Increment quantity instead of adding new part
                    unique_part.quantity += part.quantity
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_parts.append(part)
        
        return unique_parts
```

---

### 4.5 Database Schema for Pipeline State

**Why you need a database**:
- Resume interrupted jobs
- Audit trail for debugging
- Analytics (how long does each stage take?)
- User workspace (store multiple projects)

```sql
-- Jobs table (top-level pipeline execution)
CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    file_id UUID NOT NULL REFERENCES files(id),
    status VARCHAR(20) NOT NULL,  -- 'pending', 'running', 'completed', 'failed'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Pipeline stages (track progress for each stage)
CREATE TABLE pipeline_stages (
    id UUID PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES jobs(id),
    stage_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- 'pending', 'running', 'completed', 'failed'
    progress_percent DECIMAL(5,2),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INT,
    error_message TEXT
);

-- Cached results (avoid reprocessing)
CREATE TABLE cached_stage_results (
    id UUID PRIMARY KEY,
    input_hash VARCHAR(64) NOT NULL UNIQUE,
    stage_name VARCHAR(50) NOT NULL,
    output_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX (input_hash, stage_name)
);

-- Parts table (store extracted parts)
CREATE TABLE parts (
    id UUID PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES jobs(id),
    part_id VARCHAR(50) NOT NULL,
    classification VARCHAR(20),
    quantity INT,
    volume DECIMAL(10,2),
    svg_drawing TEXT,
    metrics JSONB,
    deduplication_group_id UUID,
    created_at TIMESTAMP
);

-- Assembly steps (final output)
CREATE TABLE assembly_steps (
    id UUID PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES jobs(id),
    step_number INT,
    title VARCHAR(200),
    description TEXT,
    part_indices JSONB,  -- [0, 1, 5]
    context_indices JSONB,  -- []
    svg_diagram TEXT,
    estimated_time_min INT,
    difficulty VARCHAR(20)
);
```

---

## 5. Recommended Architecture for WEBLE

### 5.1 Complete Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ API Layer (FastAPI Routes)                           │   │
│  │ - POST /api/step/upload                              │   │
│  │ - POST /api/step/parts-2d                            │   │
│  │ - POST /api/step/assembly-analysis                   │   │
│  │ - GET /api/jobs/{id}/progress (SSE)                  │   │
│  └────────────┬─────────────────────────────────────────┘   │
│               │                                              │
│  ┌────────────▼─────────────────────────────────────────┐   │
│  │ Pipeline Orchestrator                                │   │
│  │ - Manages job state                                  │   │
│  │ - Coordinates stages                                 │   │
│  │ - Handles retries and error recovery                 │   │
│  └────────────┬─────────────────────────────────────────┘   │
│               │                                              │
│  ┌────────────┴─────────────────────────────────────────┐   │
│  │ Reusable Processing Stages                           │   │
│  │ - Stage 1: Step File Loading (CadQuery)              │   │
│  │ - Stage 2: Parts Extraction & Classification         │   │
│  │ - Stage 3: 2D Drawing Generation (HLR)               │   │
│  │ - Stage 4: Assembly Instruction Generation (LLM)     │   │
│  └────────────┬─────────────────────────────────────────┘   │
│               │                                              │
│  ┌────────────▼─────────────────────────────────────────┐   │
│  │ Data & Infrastructure Services                       │   │
│  │ - Database (PostgreSQL)                              │   │
│  │ - Cache (Redis)                                      │   │
│  │ - File Storage (S3)                                  │   │
│  │ - Message Queue (Celery/RabbitMQ for async jobs)     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │ (SSE Progress)
                           │
┌──────────────────────────┴─────────────────────────────────┐
│                   React Frontend                            │
│ - 3D Visualization (Three.js)                              │
│ - Progress Display                                         │
│ - Step Viewer & Assembly Instructions                      │
└────────────────────────────────────────────────────────────┘
```

### 5.2 Code Organization

```
backend/
├── app/
│   ├── main.py                 # FastAPI app setup
│   ├── api/
│   │   └── routes.py           # /api/step/* endpoints
│   ├── services/
│   │   ├── pipeline.py         # Pipeline orchestrator
│   │   ├── job_manager.py      # Job state management
│   │   └── progress_tracker.py # Progress emission
│   ├── processors/             # Reusable stage implementations
│   │   ├── step_loader.py      # Stage 1: STEP → Geometry
│   │   ├── parts_extractor.py  # Stage 2: Geometry → Parts
│   │   ├── drawing_generator.py  # Stage 3: Parts → SVG
│   │   └── assembly_generator.py # Stage 4: SVG → Steps
│   ├── models/
│   │   ├── geometry.py         # RawGeometry, Solid, Face
│   │   ├── parts.py            # Part, PartsList
│   │   └── assembly.py         # AssemblyStep, AssemblySteps
│   ├── infrastructure/
│   │   ├── database.py         # Database models
│   │   ├── cache.py            # Redis/cache layer
│   │   ├── storage.py          # S3/file storage
│   │   └── events.py           # SSE event broadcast
│   └── core/
│       ├── config.py           # Config/env vars
│       ├── exceptions.py       # Custom exceptions
│       └── logger.py           # Structured logging
├── tests/
│   ├── test_step_loader.py
│   ├── test_parts_extractor.py
│   ├── test_drawing_generator.py
│   ├── test_assembly_generator.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
├── Dockerfile
└── .env.example
```

### 5.3 Key Technologies

| Component | Technology | Why |
|-----------|-----------|-----|
| **Web Framework** | FastAPI | Async-first, automatic OpenAPI docs |
| **CAD Processing** | CadQuery + OpenCASCADE | STEP parsing, geometry, topology |
| **Mesh Optimization** | Trimesh | Decimation, analysis |
| **2D Drawings** | OpenCASCADE HLR + SVG | Professional technical drawings |
| **LLM Integration** | OpenRouter/Anthropic | Multi-model support, cost optimization |
| **Database** | PostgreSQL | Reliable, JSONB for flexible metadata |
| **Cache** | Redis | Fast, distributed, perfect for stage results |
| **File Storage** | S3-compatible (MinIO dev, AWS prod) | Scalable, reliable |
| **Job Queue** | Celery + RabbitMQ | Async task processing |
| **Progress Tracking** | Server-Sent Events (SSE) | Real-time updates to frontend |
| **Monitoring** | Prometheus + Grafana | Production observability |

---

## 6. Development Roadmap & Priorities

### **Phase 1: Core Pipeline (Weeks 1-3)**
- ✅ Stage 1: STEP file loading with CadQuery
- ✅ Stage 2: Parts extraction and classification
- ✅ Progress tracking via SSE
- ✅ Basic error handling

### **Phase 2: Visual Quality (Weeks 4-6)**
- ✅ Stage 3: 2D SVG drawing generation (HLR)
- ✅ Three.js 3D visualization
- ✅ Part grouping and deduplication UI

### **Phase 3: Assembly Intelligence (Weeks 7-9)**
- ✅ Stage 4: LLM-based assembly instruction generation
- ✅ Structured prompting for consistency
- ✅ Validation of generated steps

### **Phase 4: Production Readiness (Weeks 10-12)**
- ✅ Caching layer (Redis)
- ✅ Database schema and persistence
- ✅ Async job queue (Celery)
- ✅ Error recovery and retry logic
- ✅ Production deployment

---

## 7. References & Further Reading

### **CAD Libraries**
- [CadQuery Documentation](https://cadquery.readthedocs.io/)
- [OpenCASCADE Technology](https://www.opencascade.com/)
- [Trimesh Documentation](https://trimesh.org/)
- [PyOCP (Python Bindings for OCP)](https://github.com/CadQuery/OCP)

### **Design Patterns**
- Martin Fowler: "Enterprise Integration Patterns"
- Sam Newman: "Building Microservices"
- Release It! (Michael Nygard) - Circuit breaker, bulkhead patterns

### **Python Async & FastAPI**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ASGI Specification](https://asgi.readthedocs.io/)
- [Real Python: Async IO](https://realpython.com/async-io-python/)

### **CAD Processing**
- [IEEE: Geometric Algorithms for CAD](https://ieeexplore.ieee.org/)
- STEP ISO 10303 Standard
- Autodesk ACIS Reference
- Parasolid Reference

### **Production Patterns**
- [Google SRE Book](https://sre.google/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/)
- Circuit Breaker: [Martin Fowler](https://martinfowler.com/bliki/CircuitBreaker.html)

---

**Document Prepared**: April 10, 2026
**Status**: Ready for implementation planning
