# WEBLE Quick Reference: Stage Data Flow

**One-page cheat sheet for developers implementing the pipeline**

---

## Stage 1: STEP Loading → RawGeometry

**What it does**: Reads STEP file, extracts geometry

**Input**: 
```
file_path: str  # Path to .step or .stp file
```

**Output**:
```python
RawGeometry(
    model_id="sha256hash",
    triangulated_mesh={
        "vertices": float32[n, 3],      # n vertices
        "normals": float32[n, 3],       # Per-vertex normals
        "indices": uint32[m]            # m triangle indices
    },
    bounding_box={
        "min": {"x": 0, "y": 0, "z": 0},
        "max": {"x": 100, "y": 200, "z": 150}
    },
    solids=[
        {solid_id, face_count, volume, centroid, bounding_box},
        ...
    ]
)
```

**Processing time**: 2-30s (depends on file size)

**Library**: CadQuery + OpenCASCADE

**Key formula**: Volume-based deduplication uses:
```python
ratio = max(v1, v2) / min(v1, v2)
if ratio <= 1.15:  # Within 15%
    parts_are_similar = True
```

---

## Stage 2: Parts Extraction → PartsList

**What it does**: Classify parts, group duplicates, assign IDs

**Input**: RawGeometry (from Stage 1)

**Output**:
```python
PartsList(
    model_id="sha256hash",
    parts=[
        Part(
            part_id="part_A",           # Letter-based ID
            solid_ids=["solid_0"],      # Reference to Stage 1
            quantity=1,
            classification="panel",      # panel|hardware|fastener|structural|other
            metrics={
                volume=1234.56,
                dimensions={width, height, depth},
                bounding_box={...},
                centroid=(x, y, z)
            }
        ),
        Part(
            part_id="part_B",
            solid_ids=["solid_1", "solid_2", "solid_3"],  # Grouped!
            quantity=3,
            classification="fastener",
            metrics={...}
        )
    ]
)
```

**Processing time**: 1-10s

**Classification logic**:
```python
if aspect_ratio > 10 and depth < 5:
    return "panel"  # Large, thin

elif volume < 50:
    return "fastener"  # Small

elif 50 < volume < 500:
    return "hardware"  # Medium

elif volume > 500 and all_dimensions > 10:
    return "structural"  # Large, balanced

else:
    return "other"
```

---

## Stage 3: 2D Drawing Generation → PartsWithDrawings

**What it does**: Generate isometric SVG drawings for each unique part

**Input**: PartsList (from Stage 2)

**Output**:
```python
PartsWithDrawings(
    model_id="sha256hash",
    parts=[
        Part(
            part_id="part_A",
            ...metadata from Stage 2...,
            svg_drawing="""<svg width="200" height="200">
                <g id="part_A_drawing">
                    <polygon points="..."/>
                    <text>Qty: 1</text>
                </g>
            </svg>"""
        ),
        ...
    ]
)
```

**Processing time**: 1-5s per part (expensive!)

**Cache key**: (part_id, classification, dimensions)
- If you've seen this exact part before, reuse its SVG

**Library**: OpenCASCADE HLR (Hidden Line Removal) + SVG generation

---

## Stage 4: Assembly Instructions → AssemblySteps

**What it does**: Generate logical assembly sequence with AI

**Input**: PartsWithDrawings (from Stage 3) + part connectivity analysis

**Output**:
```python
AssemblySteps(
    model_id="sha256hash",
    steps=[
        AssemblyStep(
            step_number=1,
            title="Assemble base frame",
            description="Connect left side panel (A) to bottom shelf (B) using 4 dowels...",
            part_indices=[0, 5],        # Indices into parts list
            part_roles={"0": "side panel", "5": "dowel"},
            context_part_indices=[],    # No context for first step
            exploded_view_svg="<svg>...</svg>",
            estimated_time_minutes=5,
            difficulty="easy",
            tools=["mallet"]
        ),
        AssemblyStep(
            step_number=2,
            title="Attach back panel",
            part_indices=[2],
            part_roles={"2": "back panel"},
            context_part_indices=[0, 5],  # Show previously assembled parts
            ...
        )
    ]
)
```

**Processing time**: 10-30s (mostly waiting for LLM API)

**LLM Prompt Template**:
```
You are an IKEA assembly instruction generator.

PARTS LIST:
- part_A (qty 1): Side panel, wood, 100×200×2mm
- part_B (qty 4): Wooden dowel, diameter 8mm
- part_C (qty 1): Back panel, wood, 100×200×2mm
- ...

SPATIAL RELATIONSHIPS:
- Part A and B are adjacent (dowels fit into side panel grooves)
- Part C connects to parts A and B (slides into grooves)
- ...

Generate assembly steps in JSON format:
{
  "steps": [
    {
      "stepNumber": 1,
      "title": "...",
      "description": "...",
      "partIndices": [...],
      ...
    }
  ]
}
```

**Error handling**:
- If LLM times out → Use fallback template with generic instructions
- If LLM returns invalid JSON → Log error, ask user for manual review
- If part reference is invalid → Validation step catches it before DB

---

## Data Dependency Graph

```
Stage 1 Output (RawGeometry)
├─ model_id ──────────┐
├─ solids ────────────┤
│  ├─ solid_id        │
│  ├─ volume ─────┐   │
│  ├─ bounding_box│   │
│  └─ centroid    │   │
├─ triangulated_mesh  │
│  ├─ vertices ────────┼────→ Frontend (Three.js rendering)
│  ├─ normals         │
│  └─ indices ────────┘
│
└─→ Stage 2 (Parts Extraction)
     │
     ├─ Uses: solid_id, volume, bounding_box, centroid
     │
     └─→ Output: PartsList with classifications
         │
         └─→ Stage 3 (2D Drawing Generation)
              │
              ├─ Uses: part_id, solid_ids, metrics
              │
              └─→ Output: PartsWithDrawings with SVGs
                  │
                  └─→ Stage 4 (Assembly Generation)
                       │
                       ├─ Uses: part_id, classification, metrics, svg_drawing
                       │
                       └─→ Output: AssemblySteps
                           │
                           └─→ Frontend (Display instructions)
```

---

## Common Mistakes & Fixes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Losing solid_id between stages | Can't link parts back to geometry | Store in PartsList, pass through |
| Wrong tolerance values | Parts that should be grouped aren't | Use 15% as default, make configurable |
| Generating SVG in DB query | Slow page loads | Generate on-demand, cache in Redis |
| Not validating LLM output | Crashes when parsing JSON | Parse → validate → use or fallback |
| Processing all parts serially | Slow for 1000+ parts | Use asyncio.gather() for parallelization |
| Storing full geometry in DB | DB bloats, slow | Store only metadata, geometry in S3 |

---

## Testing Checklist Per Stage

### Stage 1 Tests
- [ ] Load valid STEP file
- [ ] Handle corrupted STEP file
- [ ] File size limit enforcement
- [ ] Verify vertex/normal/index arrays
- [ ] Verify bounding box calculation
- [ ] Hash consistency (same file = same hash)

### Stage 2 Tests
- [ ] Panel detection (volume + aspect ratio)
- [ ] Fastener detection (volume < 50)
- [ ] Deduplication within tolerance
- [ ] Part ID generation and uniqueness
- [ ] Quantity increment on grouping

### Stage 3 Tests
- [ ] SVG generation for each unique part
- [ ] SVG cache hits / misses
- [ ] Quantity notation (×12) rendering
- [ ] Isometric projection correctness

### Stage 4 Tests
- [ ] LLM prompt construction
- [ ] JSON parsing from LLM response
- [ ] Part index validation
- [ ] Context part selection logic
- [ ] Fallback template on LLM failure

---

## Performance Targets

| Stage | Target Time | Constraint | Notes |
|-------|-------------|-----------|-------|
| Stage 1 | 2-10s | File I/O, geometry complexity | STEP parsing bottleneck |
| Stage 2 | 1-5s | Part count, deduplication | Linear in parts |
| Stage 3 | 5-30s | Part uniqueness, SVG complexity | Expensive, high cache value |
| Stage 4 | 10-30s | LLM API latency | Mostly waiting for API |
| **Total** | **20-75s** | File size < 20MB | Typical furniture |

**If total > 60s**: Show progress bar, not frozen UI

---

## Database Schema Essentials

```sql
-- Jobs track overall pipeline execution
CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    model_id VARCHAR(64),        -- Links to all stages
    user_id UUID,
    status VARCHAR(20),          -- pending, running, completed, failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Cache to avoid reprocessing
CREATE TABLE cache_stage_results (
    input_hash VARCHAR(64) PRIMARY KEY,
    stage_name VARCHAR(50),
    output_data JSONB,           -- Full stage output
    created_at TIMESTAMP
);

-- Parts for reference
CREATE TABLE parts (
    id UUID PRIMARY KEY,
    model_id VARCHAR(64),
    part_id VARCHAR(10),         -- A, B, C, ...
    classification VARCHAR(20),
    quantity INT,
    svg_drawing TEXT
);
```

---

**Last Updated**: April 10, 2026
**For**: Implementation team
**Status**: Ready to code
