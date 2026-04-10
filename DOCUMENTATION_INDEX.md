# WEBLE Architecture Research: Complete Index

**Comprehensive research on CAD processing pipelines, library choices, and design patterns for the WEBLE system**

Generated: April 10, 2026

---

## 📚 Documents Overview

### 1. **PIPELINE_ARCHITECTURE.md** (Main Document)
**Length**: ~800 lines | **Read time**: 45 minutes | **Audience**: Architects, Tech Leads

Comprehensive guide covering:
- **Section 1**: WEBLE pipeline stages in detail (4-stage transformation system)
  - Stage 1: STEP file → 3D Geometry
  - Stage 2: Geometry → Parts (with classification & deduplication)
  - Stage 3: Parts → 2D SVG Drawings
  - Stage 4: Drawings → Assembly Instructions
  - Data contracts between stages

- **Section 2**: Python CAD libraries comparison
  - CadQuery (recommended)
  - Trimesh, Open3D, PyOCP, commercial options
  - Detailed strengths/weaknesses table
  - Recommended stack for WEBLE

- **Section 3**: Design patterns for multi-stage pipelines
  - Pipeline pattern overview
  - Stage-based architecture
  - Error handling (retry, circuit breaker, checkpointing)
  - Caching & deduplication strategies
  - Progress tracking patterns
  - LLM integration strategies

- **Section 4**: Real-world CAD systems patterns
  - Error handling by category
  - Production progress tracking
  - Large assembly handling (10k+ parts)
  - Database schema for pipeline state

- **Section 5**: Recommended architecture for WEBLE
  - Complete pipeline diagram
  - Code organization structure
  - Technology selections justified

---

### 2. **IMPLEMENTATION_REFERENCE.md** (Code Examples)
**Length**: ~600 lines | **Read time**: 30 minutes | **Audience**: Backend Developers

Practical code implementations:

- **Stage 1 Implementation**: Complete StepLoaderStage class
  - STEP file loading with CadQuery
  - Mesh triangulation algorithm
  - Vertex normal computation
  - Solid metadata extraction
  - Input validation

- **Stage 2 Implementation**: Complete PartsExtractorStage class
  - Part extraction from solids
  - Part classification logic
  - Deduplication algorithm
  - Tolerance-based comparison

- **Data Structures**: Complete TypeScript/Python definitions
  - RawGeometry, Part, PartsList
  - AssemblyStep, AssemblySteps
  - Type safety examples

- **Configuration Templates**
  - .env file template with all variables
  - Pydantic settings class
  - Runtime configuration

- **Testing Strategies**
  - Unit test examples for deduplication
  - Classification detection tests
  - Integration test patterns

- **Performance Optimization**
  - Benchmarking framework
  - Memory optimization for large assemblies
  - Streaming and batching patterns

---

### 3. **EXECUTIVE_SUMMARY.md** (Decision Matrix)
**Length**: ~400 lines | **Read time**: 20 minutes | **Audience**: Decision Makers, Architects

Decision-focused reference:

- **Decision Matrix Tables**
  - Sequential vs Parallel execution
  - Library choices (CadQuery vs alternatives)
  - 2D drawing generation (HLR vs SVG)
  - Progress tracking (SSE vs WebSocket vs Polling)
  - Caching strategy (Memory vs Redis vs Disk)
  - Error handling (Fail-fast vs Graceful degradation)

- **Data Transformation Flow**
  - Visual diagram of 4-stage pipeline
  - Data contracts between stages
  - Critical information passed at each boundary

- **Performance Profiles**
  - Time estimates by file size
  - Bottleneck analysis
  - Optimization priorities by phase

- **Tech Stack Justification**
  - Backend: FastAPI + Python (why, pros/cons, alternatives)
  - Database: PostgreSQL + Prisma
  - Frontend: Next.js + Three.js

- **Common Pitfalls**
  - Storage optimization (geometry in S3, not DB)
  - Timeout handling
  - Deduplication algorithms (O(n²) vs O(n log n))
  - Large file handling

- **Architecture Strengths**
  - Maintainability
  - Performance
  - Resilience
  - User experience
  - Operational safety

---

### 4. **QUICK_REFERENCE.md** (Developer Cheat Sheet)
**Length**: ~300 lines | **Read time**: 10 minutes | **Audience**: Implementation Team

One-page reference for daily development:

- **Stage-by-Stage Summary**
  - Input/output format for each stage
  - Processing time estimates
  - Key formulas and logic

- **Data Dependency Graph**
  - Visual representation of data flow
  - Which data flows where

- **Common Mistakes & Fixes**
  - Quick lookup table of errors
  - Immediate remediation

- **Testing Checklist**
  - What to test per stage
  - Critical test scenarios

- **Performance Targets**
  - SLA per stage
  - Total system SLA

- **Database Schema Essentials**
  - Minimal SQL needed for tracking
  - Cache table for redundancy prevention

---

## 🎯 Reading Paths by Role

### **For System Architects** (→ New to project)
1. Start: EXECUTIVE_SUMMARY.md (20 min) - Get the big picture
2. Deep dive: PIPELINE_ARCHITECTURE.md (45 min) - Understand design
3. Reference: QUICK_REFERENCE.md (5 min) - Bookmark for later

### **For Backend Developers** (→ Implementing stages)
1. Start: QUICK_REFERENCE.md (10 min) - Understand data flow
2. Deep dive: IMPLEMENTATION_REFERENCE.md (30 min) - See code examples
3. Reference: PIPELINE_ARCHITECTURE.md sections 3-4 (30 min) - Patterns
4. Daily: QUICK_REFERENCE.md - Cheat sheet

### **For Tech Leads / Decision Makers**
1. Start: EXECUTIVE_SUMMARY.md (20 min) - All decisions justified
2. Reference: PIPELINE_ARCHITECTURE.md section 5 (15 min) - Architecture
3. Deep dives: As needed for specific decisions

### **For Frontend Developers**
1. Quick read: QUICK_REFERENCE.md (10 min) - Data structures
2. Reference: PIPELINE_ARCHITECTURE.md section 1.4-1.5 (15 min) - Front-end integration
3. Implementation details: IMPLEMENTATION_REFERENCE.md section on data structures

---

## 📊 Key Findings Summary

### 1. WEBLE Pipeline Structure
```
STEP File 
  ↓ [CadQuery - 2-30s]
Raw Geometry (vertices, topology, solids)
  ↓ [Custom classifier - 1-10s]
Parts List (with classifications & quantities)
  ↓ [OpenCASCADE HLR - 5-30s]
Parts with 2D SVG Drawings
  ↓ [LLM API - 10-30s]
Assembly Steps (ordered, with instructions)
  ↓ [Frontend - Real-time rendering]
User-friendly IKEA-style instructions
```

### 2. Recommended Libraries
| Task | Library | Why |
|------|---------|-----|
| STEP parsing | CadQuery | Best Python CAD API |
| Mesh optimization | Trimesh | Fast, simple, mature |
| 2D technical drawings | OpenCASCADE HLR | Professional quality |
| 3D visualization | Three.js | Industry standard for web |
| Progress tracking | Server-Sent Events | Simple, one-way, efficient |

### 3. Critical Design Patterns
1. **Pipeline Pattern**: Sequential stages with explicit data contracts
2. **Error Handling**: Graceful degradation where possible, fail-fast for unrecoverable errors
3. **Caching**: Two-tier (memory + Redis) to avoid expensive reprocessing
4. **Progress Tracking**: SSE for real-time feedback without polling
5. **Resilience**: Retry logic, circuit breaker, checkpointing for interruption recovery

### 4. Data Contracts Are Critical
- Each stage MUST preserve specific data for the next stage
- Part IDs must be stable (A, B, C...) throughout pipeline
- Centroids and volumes are essential for deduplication (15% tolerance)
- Solid IDs enable traceability back to original geometry

### 5. Performance Bottlenecks (in priority order)
1. **Stage 3 (SVG generation)**: 5-30s per unique part → Heavy caching required
2. **Stage 4 (LLM API)**: 10-30s → Network latency, has fallback
3. **Stage 2 (Deduplication)**: O(n²) without optimization → Use sort + compare
4. **Stage 1 (STEP parsing)**: Depends on file size → Async thread pool

### 6. Tolerance Values
- **Volume comparison**: 15% (±15% matches considered identical)
- **Dimension comparison**: 15% (same threshold)
- **Why 15%**: Balances false positives (5% too strict) vs false negatives (25% too loose)

---

## 🔧 Implementation Roadmap

### Phase 1: Core Pipeline (MVP - 2-3 weeks)
- [ ] Stage 1: STEP loading (CadQuery)
- [ ] Stage 2: Parts extraction (basic classification)
- [ ] SSE progress tracking
- [ ] Basic error handling
- **Deliverable**: Load a STEP file, extract parts, show progress

### Phase 2: Visual Quality (2-3 weeks)
- [ ] Stage 3: 2D SVG generation (HLR)
- [ ] Three.js 3D visualization
- [ ] Frontend UI for part viewer
- **Deliverable**: Beautiful technical drawings and 3D visualization

### Phase 3: Assembly Intelligence (2-3 weeks)
- [ ] Stage 4: LLM-based instructions
- [ ] Structured prompting
- [ ] Validation of generated steps
- [ ] Step viewer UI
- **Deliverable**: Step-by-step assembly instructions

### Phase 4: Production Ready (2-3 weeks)
- [ ] Database persistence (PostgreSQL + Prisma)
- [ ] Caching layer (Redis)
- [ ] Error recovery (retry logic, circuit breaker)
- [ ] Async job queue (Celery)
- [ ] Comprehensive testing
- [ ] Deployment setup
- **Deliverable**: Production-ready system

---

## 📈 Performance Expectations

| File Size | Total Time | Quality | Notes |
|-----------|-----------|---------|-------|
| < 1 MB | 15-30 sec | High | Fast feedback |
| 1-5 MB | 30-60 sec | High | Good user experience |
| 5-20 MB | 60-120 sec | High | Show progress bar |
| 20-100 MB | 2-5 min | Degraded | Stream results, large parts get simplified |
| > 100 MB | Not recommended | Very degraded | Requires special handling |

---

## ✅ Validation Checklist

Before moving to production, validate:

- [ ] STEP files from multiple CAD tools (Fusion360, SolidWorks, FreeCAD, etc.)
- [ ] File sizes from 100KB to 50MB
- [ ] Assemblies with 10 to 5000 parts
- [ ] Various part types (panels, hardware, fasteners, structural)
- [ ] Error conditions (corrupted files, timeouts, API failures)
- [ ] Progress tracking accuracy
- [ ] Cache effectiveness (hit rates > 80%)
- [ ] Large file handling (no crashes, streaming works)
- [ ] Assembly instruction quality (validated by furniture assembly experts)

---

## 🚀 Quick Start Commands

```bash
# Clone repo
git clone https://github.com/yourusername/weble.git
cd weble

# Read documentation
cat QUICK_REFERENCE.md              # 5 min overview
cat PIPELINE_ARCHITECTURE.md        # 45 min deep dive
cat IMPLEMENTATION_REFERENCE.md     # Code examples

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Add Stage 1 implementation (see IMPLEMENTATION_REFERENCE.md)

# Start backend
python -m uvicorn app.main:app --reload

# Frontend setup
cd ../frontend
npm install
npm run dev

# Test a stage
python -m pytest tests/test_parts_extractor.py -v
```

---

## 📞 Key Contacts for Questions

### By Topic
| Topic | Reference | Section |
|-------|-----------|---------|
| Library decisions | EXECUTIVE_SUMMARY.md | Tech Stack Justification |
| Error handling | PIPELINE_ARCHITECTURE.md | Section 4.1 |
| Progress tracking | PIPELINE_ARCHITECTURE.md | Section 3.5 |
| LLM integration | PIPELINE_ARCHITECTURE.md | Section 4.3 |
| Code examples | IMPLEMENTATION_REFERENCE.md | All sections |
| Performance targets | EXECUTIVE_SUMMARY.md | Performance Profiles |
| Data contracts | QUICK_REFERENCE.md | Data Dependency Graph |

---

## 🎓 Learning Resources

### Recommended Reading Order
1. **Pipeline Pattern**: Enterprise Integration Patterns (Hohpe & Woolf)
2. **CAD Geometry**: "Computational Geometry" (de Berg et al.)
3. **Async Python**: Real Python's Async IO tutorial
4. **FastAPI**: Official FastAPI docs (better than any book)
5. **Three.js**: Official Three.js docs + examples

### Key Standards
- STEP/ISO 10303: CAD file format specification
- OpenCASCADE: Open-source CAD kernel documentation
- WebGL/Three.js: 3D graphics in browser
- ASGI: Async Python web standard

---

## 📝 Document Maintenance

**These documents should be updated when**:
- Architecture decisions change
- New libraries are adopted
- Performance characteristics shift
- Error patterns emerge in production
- New insights from user feedback

**Frequency**: Quarterly review or when major change occurs

**Owner**: Tech Lead / Architecture Team

---

## 🔍 Document Quality Checklist

- [x] Complete coverage of all 4 stages
- [x] Data contracts explicitly defined
- [x] Library choices justified with pros/cons
- [x] Design patterns documented with examples
- [x] Production patterns from real CAD systems
- [x] Code examples (Python + JavaScript)
- [x] Performance targets and expectations
- [x] Error handling strategies
- [x] Testing approaches
- [x] Deployment considerations
- [x] Quick reference for daily development
- [x] Executive summary for decisions

---

**Status**: ✅ Complete and ready for implementation

**Total Content**: ~2,000 lines across 4 documents

**Estimated Setup Time**: 2-3 hours to read and understand

**Next Step**: Begin Phase 1 implementation with IMPLEMENTATION_REFERENCE.md
