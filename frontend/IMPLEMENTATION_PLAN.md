# WEBLE Frontend Revised Implementation Plan

**Status**: Analysis Phase - Understanding backend data formats

## Current Understanding from User

### 3D Viewer Requirements
- Display full assembled furniture model (explodable)
- Allow rotate/zoom with OrbitControls
- Hover preview of parts with caching (prevent freezeups)
- Click to highlight part (color/glow)
- Highlight sync: click part card → highlights in 3D and vice versa
- Step-aware highlighting: on Assembly page, only highlight parts for current step

### Page Layouts

#### Progress+Viewer Page (`/progress/[jobId]`)
- Real-time SSE progress with animated skeletons
- Auto-transition to 3D viewer on completion
- 3D model ready for interaction

#### Parts Page (`/parts/[modelId]`)
- **Two-column layout**:
  - Left: Large 3D viewer (highlight-on-hover)
  - Right: Vertical scrollable parts list
- Hover context menu on left showing part details
- Hover part card → Part highlights in 3D with caching
- Synced selection between 3D and list

#### Assembly Page (`/assembly/[modelId]`)
- 3D viewer + step carousel
- Step navigation → updates 3D highlighting
- Shows cumulative assembly state (parts assembled so far)
- No 3D screenshots in PDF export (text + 2D SVG diagrams only)

### Design Requirements
- **Squircle corners**: Apply to ALL interactive elements (buttons, cards, inputs, alerts, badges)
- **No border colors**: Use light fill colors + shadows instead
- **Hover previews**: Cache parts to prevent performance issues during hover

---

## Tasks

### Task 1: Analyze Backend Data Structures
- [ ] Check what `GET /api/v1/step/{model_id}` returns
- [ ] Check what `POST /api/v1/step/parts-2d` returns
- [ ] Check what `POST /api/v1/step/assembly-analysis` returns
- [ ] Determine part identification scheme (indices, material IDs, separate meshes?)
- [ ] Determine geometry format (GLB, raw arrays, per-part data?)
- [ ] Determine assembly sequencing (how parts are ordered in steps)

### Task 2: Fix API Integration
- [ ] Update `services/api.ts` endpoints to match backend
- [ ] Map backend response fields to frontend expectations
- [ ] Create proper type definitions matching backend responses
- [ ] Handle geometry data correctly

### Task 3: Rebuild 3D Viewer Component
- [ ] Load full assembled model from backend geometry
- [ ] Implement part-level mesh management (identify individual parts)
- [ ] Implement OrbitControls (rotate/zoom)
- [ ] Implement explode/collapse animation
- [ ] Implement hover preview caching system
- [ ] Implement part selection/highlighting (color or glow)
- [ ] Add event callbacks for click/hover sync

### Task 4: Rebuild Parts Page
- [ ] Create two-column layout (3D viewer + parts list)
- [ ] Create PartHoverPreview component (context menu)
- [ ] Sync 3D viewer with parts selection
- [ ] Implement caching to prevent performance issues

### Task 5: Rebuild Assembly Page
- [ ] Create AssemblyViewer component (3D + step carousel)
- [ ] Implement step-aware highlighting
- [ ] Show cumulative assembly progression
- [ ] Sync 3D with step navigation

### Task 6: Fix UI Design
- [ ] Apply squircle corners consistently
- [ ] Replace all sharp border colors with light fills/shadows
- [ ] Override shadcn component defaults for rounded corners
- [ ] Ensure smooth, soft Apple-like aesthetic

### Task 7: Performance Optimization
- [ ] Optimize 3D rendering (cull hidden parts, use instancing if needed)
- [ ] Implement hover preview caching correctly
- [ ] Test under load with large assemblies

---

## Backend Data Format (To Be Determined)

### Key Questions
1. What does `GET /api/v1/step/{model_id}` return?
2. How are parts identified in the geometry (indices, separate meshes, etc.)?
3. What assembly order information is provided?
4. Is geometry a GLB file or raw arrays?

### Expected Responses (Hypothesis)
- `GET /api/v1/step/{model_id}` → Geometry + part metadata
- `POST /api/v1/step/parts-2d` → Parts array with metadata
- `POST /api/v1/step/assembly-analysis` → Steps array with part indices

---

## Component Structure (Revised)

```
frontend/
├── components/custom/
│   ├── GeometryViewer.tsx          # Rewritten: Part mesh management, OrbitControls, explode
│   ├── PartHoverPreview.tsx        # New: Context menu popup on parts list
│   ├── PartsViewer.tsx             # New: Two-column layout wrapper
│   ├── AssemblyViewer.tsx          # New: 3D + step carousel combo
│   └── SkeletonComponents.tsx      # Updated: New layout skeletons
│
├── app/
│   ├── progress/[jobId]/page.tsx   # Updated: Add 3D viewer to merge page
│   ├── parts/[modelId]/page.tsx    # Rewritten: Two-column layout
│   └── assembly/[modelId]/page.tsx # Rewritten: With AssemblyViewer
│
├── hooks/
│   ├── useProgress.ts              # Existing: SSE hook
│   ├── use3DViewer.ts              # New: Geometry loading + caching
│   └── usePartSelection.ts         # New: Part selection state
│
└── types/
    └── index.ts                    # Updated: New geometry/part types
```

---

## Phase Breakdown

**Phase 1**: Backend Analysis + API Fixes (CURRENT)
**Phase 2**: 3D Viewer Rebuild
**Phase 3**: Parts Page Restructure
**Phase 4**: Assembly Page Restructure
**Phase 5**: UI Polish (Squircles + Colors)
**Phase 6**: Performance Optimization

---

## Notes

- User wants backend to provide as much data as possible
- Frontend should not generate PDFs with 3D screenshots (text + 2D SVG only)
- Caching is critical for hover preview performance
- Part highlighting should be synchronized between 3D and UI list
- Assembly page should show cumulative state (parts assembled so far in current step)
