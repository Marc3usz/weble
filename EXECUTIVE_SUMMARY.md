# WEBLE Architecture: Executive Summary & Decision Matrix

**Quick reference guide for architecture decisions and trade-offs**

---

## Quick Decision Matrix

### 1. Pipeline Execution: Sequential vs Parallel

| Aspect | Sequential | Parallel | Decision |
|--------|-----------|----------|----------|
| Simplicity | ✅ Simple | ❌ Complex | Sequential |
| Data Dependencies | ✅ None | ❌ Stage 2 needs Stage 1 output | Sequential |
| Resource Usage | ⚠️ More total time | ✅ Faster | Sequential (easier to reason about) |
| Error Recovery | ✅ Easy | ❌ Harder to rollback | Sequential |
| **Recommendation** | **CHOOSE** | Next phase | - |

**Why Sequential**: Each stage requires complete output from previous stage. Parallelization only helps if you process multiple files simultaneously.

---

### 2. Library Choice: CadQuery vs PyOCP vs OCP

| Criterion | CadQuery | PyOCP | OCP | Decision |
|-----------|----------|-------|-----|----------|
| STEP Parsing | ✅ Built-in | ⚠️ Low-level | ⚠️ Raw bindings | **CadQuery** |
| Part Extraction | ✅ Easy | ⚠️ Medium | ⚠️ Hard | **CadQuery** |
| Documentation | ✅ Excellent | ⚠️ Sparse | ❌ Poor | **CadQuery** |
| Community | ✅ Active | ⚠️ Small | ❌ Tiny | **CadQuery** |
| Learning Curve | ✅ Gentle | ⚠️ Steep | ❌ Very steep | **CadQuery** |
| **Recommendation** | **USE** | - | - | - |

**Why CadQuery**: Professional-grade abstraction over OpenCASCADE. Best Python CAD library available.

---

### 3.2D Drawing Generation: OpenCASCADE HLR vs SVG-from-meshes

| Method | HLR | SVG from meshes | Decision |
|--------|-----|-----------------|----------|
| Visual Quality | ✅ Professional | ⚠️ Good | **HLR** |
| Accuracy | ✅ Perfect | ⚠️ Approximation | **HLR** |
| Implementation | ⚠️ Complex | ✅ Simple | Trade-off |
| Performance | ⚠️ Slower | ✅ Faster | Trade-off |
| Industry Standard | ✅ Yes | ❌ No | **HLR** |
| **Recommendation** | **USE HLR** | Fall-back only | - |

**Why HLR**: IKEA-style technical drawings require proper hidden line removal. Users expect professional quality.

---

### 4. Progress Tracking: SSE vs WebSocket vs Polling

| Method | SSE | WebSocket | Polling | Decision |
|--------|-----|-----------|---------|----------|
| Simplicity | ✅ Simple | ⚠️ Bidirectional overkill | ✅ Simple |  **SSE** |
| Server Load | ✅ Low | ⚠️ Higher | ❌ Inefficient | **SSE** |
| Real-time Feel | ✅ Good | ✅ Excellent | ⚠️ Laggy | **SSE** |
| Browser Support | ✅ Modern browsers | ✅ All | ✅ All | **SSE** |
| **Recommendation** | **USE** | - | - | - |

**Why SSE**: One-way communication from server (upload progress). No need for bidirectional messaging. Clean, efficient, built into browsers.

---

### 5. Caching Strategy: Memory vs Redis vs Disk

| Layer | Memory | Redis | Disk | Decision |
|-------|--------|-------|------|----------|
| Speed | ✅ Fastest | ✅ Fast | ⚠️ Slow | Memory first |
| Persistence | ❌ Lost on restart | ✅ Survives restarts | ✅ Yes | Redis for multi-instance |
| Scalability | ⚠️ Single process | ✅ Distributed | ⚠️ Single server | Redis for production |
| Setup Complexity | ✅ None | ⚠️ Medium | ✅ Simple | Redis balance |
| **Recommendation for Phase 1** | **START** | - | - | - |
| **Recommendation for Phase 3** | Bypass | **ADD** | - | - |

**Why Redis in production**: Multi-instance deployments need shared cache. Survives server restarts.

---

### 6. Error Handling: Fail-Fast vs Graceful Degradation

| Scenario | Fail-Fast | Degrade | Decision |
|----------|-----------|---------|----------|
| **Invalid STEP file** | ✅ Reject | ❌ Misleading | **Fail** |
| **Geometric errors** (self-intersections, degenerate faces) | ⚠️ Blocks pipeline | ✅ Skip parts, continue | **Degrade** |
| **LLM API timeout** | ⚠️ No instructions | ✅ Provide template | **Degrade** |
| **Out of memory** | ⚠️ Lose work | ✅ Downsample geometry | **Degrade** |
| **Database connection lost** | ✅ Clear error | ⚠️ Confusing | **Fail** |
| **Large assembly (>100k parts)** | ❌ Timeout | ✅ Stream results | **Degrade** |
| **Recommendation** | - | **Hybrid approach** | - |

**Why Hybrid**: User data loss is worse than errors. Degrade when possible, fail only for unrecoverable issues.

---

## Data Transformation Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│ STEP FILE (binary)                                                  │
│ - Solids with topology                                              │
│ - Face adjacency information                                        │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────┐
          │ STAGE 1: Step Loading        │
          │ (CadQuery)                   │
          │                              │
          │ Input: STEP file path        │
          │ Output: RawGeometry          │
          │ Time: 2-30 sec (depends on   │
          │       file size)             │
          │                              │
          │ Key Data Passed:             │
          │ - Triangulated vertices      │
          │ - Face normals              │
          │ - Topology (solids, faces)  │
          │ - Bounding boxes            │
          │ - Centroids, volumes        │
          └────────────────┬─────────────┘
                           │
                           ▼
          ┌──────────────────────────────┐
          │ STAGE 2: Parts Extraction    │
          │ (Custom classifier)          │
          │                              │
          │ Input: RawGeometry           │
          │ Output: PartsList            │
          │ Time: 1-10 sec               │
          │                              │
          │ Key Data Passed:             │
          │ - Part classifications       │
          │ - Quantities                 │
          │ - Metrics (volume, dims)     │
          │ - Deduplication groups       │
          └────────────────┬─────────────┘
                           │
                           ▼
          ┌──────────────────────────────┐
          │ STAGE 3: 2D Drawing Gen      │
          │ (OpenCASCADE HLR + SVG)      │
          │                              │
          │ Input: PartsList             │
          │ Output: PartsWithDrawings    │
          │ Time: 5-60 sec (per part)    │
          │                              │
          │ Key Data Passed:             │
          │ - SVG technical drawings     │
          │ - Isometric projections      │
          │ - Part outlines              │
          └────────────────┬─────────────┘
                           │
                           ▼
          ┌──────────────────────────────┐
          │ STAGE 4: Assembly Analysis   │
          │ (LLM-based instruction gen)  │
          │                              │
          │ Input: PartsWithDrawings     │
          │ Output: AssemblySteps        │
          │ Time: 10-30 sec              │
          │                              │
          │ Key Data Passed:             │
          │ - Ordered assembly steps     │
          │ - Part references            │
          │ - Instructions & diagrams    │
          │ - Tools required             │
          └────────────────┬─────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ FRONTEND DISPLAY                                                    │
│ - 3D interactive viewer                                             │
│ - Step-by-step assembly guide                                       │
│ - 2D technical drawings                                             │
│ - Estimated time & difficulty                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Critical Data Contracts Between Stages

### Stage 1 → Stage 2 Contract

```python
# Stage 1 MUST provide:
geometry_data = {
    'solids': [
        {
            'solid_id': 'solid_0',
            'volume': 1234.56,           # Critical for deduplication
            'centroid': (50, 100, 75),   # Critical for spatial analysis
            'bounding_box': {...}         # Critical for classification
        }
    ],
    'triangulated_mesh': {
        'vertices': [...],    # Flattened array for Three.js
        'normals': [...],
        'indices': [...]
    }
}

# Stage 2 depends on:
# - Accurate volume calculation (15% tolerance matching)
# - Correct bounding box (for panel detection)
# - Centroid for spatial relationships
# - Vertex count for size estimation
```

### Stage 2 → Stage 3 Contract

```python
# Stage 2 MUST provide:
parts_list = {
    'parts': [
        {
            'part_id': 'part_A',
            'solid_ids': ['solid_0'],    # Links back to Stage 1
            'classification': 'panel',
            'quantity': 1,
            'metrics': {
                'volume': 1234.56,
                'dimensions': {...}
            }
        }
    ]
}

# Stage 3 depends on:
# - Part IDs that match user's mental model
# - Accurate classification (affects drawing projection)
# - Quantity info (for ×12 notation)
# - Metrics for layout decisions
```

### Stage 3 → Stage 4 Contract

```python
# Stage 3 MUST provide:
parts_with_drawings = {
    'parts': [...],  # From Stage 2
    'svgs': {
        'part_A': '<svg>...</svg>',     # Reference in step
        'part_B': '<svg>...</svg>'
    }
}

# Stage 4 depends on:
# - SVG references for step diagrams
# - Part IDs for instruction text
# - Quantities for natural language ("add 12 screws")
# - Classifications for assembly logic
```

---

## Performance Profiles by File Size

Based on typical furniture STEP files:

| File Size | Solid Count | Est. Total Time | Bottleneck |
|-----------|------------|---|---|
| **< 1 MB** | < 50 solids | 15-30 sec | LLM API (Stage 4) |
| **1-5 MB** | 50-200 solids | 30-60 sec | Stage 3 (2D drawings) |
| **5-20 MB** | 200-500 solids | 60-120 sec | Stage 2 (classification) + Stage 3 |
| **> 20 MB** | > 500 solids | 120+ sec | Streaming needed |

**Optimization priorities**:
1. Phase 1: Get it working (any speed is ok)
2. Phase 2: Optimize Stage 1 & 2 (geometry processing is parallelizable)
3. Phase 3: Optimize Stage 3 (SVG generation is the main bottleneck)
4. Phase 4: Add caching + streaming for large files

---

## Recommended Tech Stack Justification

### Backend: FastAPI + Python

**Pros**:
- ✅ Async-first (perfect for I/O-bound CAD processing)
- ✅ Automatic OpenAPI docs
- ✅ Native SSE support for progress tracking
- ✅ Excellent async libraries (asyncio, aiofiles)
- ✅ CadQuery is Python-only

**Cons**:
- ⚠️ Not the fastest (but plenty fast for CAD)
- ⚠️ Requires proper async/await patterns

**Alternative**: Node.js + Express
- ❌ Would need to shell out to Python for CadQuery anyway
- ❌ Just adds latency and complexity

---

### Database: PostgreSQL + Prisma

**Pros**:
- ✅ JSONB type perfect for flexible schema (parts metadata)
- ✅ Excellent indexing
- ✅ Robust transaction support
- ✅ Prisma ORM is type-safe

**Cons**:
- ⚠️ More than minimum for MVP

**Alternative**: MongoDB
- ❌ JSONB is SQL, hard to query and index properly
- ❌ Transaction support is weaker

---

### Frontend: Next.js + Three.js

**Pros**:
- ✅ Next.js handles all web framework needs
- ✅ Three.js is industry standard for 3D in browser
- ✅ React Three Fiber makes 3D components composable

**Cons**:
- None significant for this use case

---

## Common Pitfalls & How to Avoid

| Pitfall | Consequence | Prevention |
|---------|-------------|-----------|
| **Storing geometry as JSON** | Bloated DB, slow queries | Store in S3, keep only IDs in DB |
| **Skipping input validation** | Crashes from bad STEP files | Validate early, provide clear errors |
| **Not handling timeouts** | Users see spinning circle forever | Set explicit timeouts per stage |
| **Hardcoding tolerances** | Wrong classification on different files | Make tolerances configurable |
| **No error recovery for LLM** | No assembly instructions if API down | Provide fallback template |
| **Processing all parts at once** | Out of memory on large files | Stream/batch processing |
| **Naive deduplication** | O(n²) slowness at 1000+ parts | Sort by volume first (O(n log n)) |
| **Storing SVGs in geometry** | Huge blobs, slow transfers | Regenerate on demand or keep separate |
| **Frontend polling for progress** | Wasted bandwidth, laggy feel | Use Server-Sent Events |

---

## Why This Architecture Wins

### ✅ Maintainability
- Clear stage separation = easy to test and modify
- Each stage has single responsibility
- Data contracts are explicit

### ✅ Performance
- Async pipeline minimizes latency
- Caching eliminates redundant work
- Streaming handles large files gracefully

### ✅ Resilience
- Graceful degradation when services fail
- Retry logic for transient errors
- Checkpointing enables resumption

### ✅ User Experience
- Real-time progress updates (SSE)
- Clear error messages with suggestions
- High-quality output (IKEA-style instructions)

### ✅ Operational Safety
- Comprehensive logging and monitoring
- Job state persistence in DB
- Easy to debug (isolated stages)

---

## Next Steps

1. **Validate with real STEP files**
   - Test with various CAD tools
   - Measure actual processing times
   - Identify performance bottlenecks

2. **Implement Stage 1 MVP**
   - STEP loader with CadQuery
   - SSE progress tracking
   - Basic error handling

3. **Iterate on part classification**
   - Train on real furniture data
   - Refine tolerance values
   - Collect user feedback

4. **Optimize visualization pipeline**
   - Profile Stage 3 (2D drawings)
   - Implement SVG caching
   - Consider WebGL-based alternatives if needed

5. **Productionize**
   - Add database persistence
   - Implement caching layer
   - Set up monitoring and alerting
   - Load testing and optimization

---

**Document Status**: Reference ready for implementation team
**Next Action**: Start with PIPELINE_ARCHITECTURE.md for detailed design
