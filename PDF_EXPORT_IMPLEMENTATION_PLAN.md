# PDF Export Implementation Plan - feat/pdf Branch

**Date Created:** April 26, 2026  
**Target Branch:** `feat/pdf`  
**Status:** Planning Phase - DETAILED SPECIFICATION  
**Last Updated:** 2026-04-26

---

## Executive Summary

Implement a complete, production-ready PDF export feature that allows users to download assembly instructions as a professional, IKEA-style manual. The PDF will include:
- Cover page with model information  
- Parts list with quantities and classifications
- Step-by-step assembly instructions with SVG diagrams
- Professional IKEA-style layout with precise typography and spacing
- Comprehensive error handling for all edge cases

**Approach:** Backend-generated PDF (Python `reportlab` library) for superior control, performance, and scalability.

**Key Design Decisions:**
1. **Backend PDF generation** - More reliable, consistent output across clients
2. **A4 page format** - Universal print compatibility
3. **Reportlab for rendering** - Mature, well-tested, good SVG support
4. **Streaming response** - Efficient memory usage for large PDFs
5. **Comprehensive validation** - All data validated before rendering

---

## Requirements Analysis

### User Stories

1. **As a user**, I want to export the full assembly manual as a PDF, so I can print it or share it offline.
2. **As a user**, I want the PDF to include all parts, assembly steps, and diagrams, so it's a complete reference.
3. **As a user**, I want professional IKEA-style formatting, so the instructions are clear and visually appealing.
4. **As a developer**, I want efficient backend PDF generation, so the service scales well.
5. **As a user**, I want immediate feedback when exporting, so I know the action is processing.
6. **As a user**, I want proper error messages if export fails, so I understand what went wrong.

### Acceptance Criteria - DETAILED

- ✅ PDF includes cover page with:
  - Model/product name
  - Generated date (ISO format)
  - Total parts count
  - Total assembly steps
  - Page number (Page 1)
- ✅ PDF includes parts list page(s) with:
  - Table: Part ID | Type | Quantity | Dimensions (mm)
  - Parts grouped by type (panels, hardware, fasteners, structural, other)
  - Sorted within each group
  - Professional table formatting with borders
  - Page numbering
- ✅ PDF includes assembly steps (one per page minimum, or combined if space allows) with:
  - Step number (e.g., "Step 1 of 12")
  - Title/heading
  - Description text (main instruction)
  - Detail description (if available from LLM)
  - Part roles with dimensions and descriptions
  - Assembly sequence (step-by-step sub-instructions if available)
  - SVG diagram embedded (exploded view if available, else basic diagram)
  - Warnings highlighted (if any)
  - Tips in callout boxes (if any)
  - Page number
- ✅ Professional IKEA-style layout:
  - Clean typography (sans-serif fonts)
  - Consistent spacing and margins
  - Proper alignment and hierarchy
  - Isometric SVG diagrams properly scaled
  - Light gray backgrounds for notes/tips
- ✅ PDF export button functional:
  - Available on Assembly page (exports all steps)
  - Available on Parts page (exports parts list)
  - Shows loading state during generation
  - Shows success/error toast notification
  - Downloads with filename: `{model_name}_assembly_manual.pdf`
- ✅ Error handling for:
  - Missing model data (404 response)
  - Empty parts list (warning in PDF)
  - Empty assembly steps (warning in PDF)
  - Invalid SVG diagrams (fallback to placeholder)
  - Large PDFs (>100 steps) - segmented rendering
  - Network errors (retry with exponential backoff)
  - Timeout (30-second max wait)
- ✅ Filename generation:
  - Extract from model metadata (file_name)
  - Sanitize special characters (only alphanumeric, dash, underscore)
  - Add timestamp if duplicate (prevent overwrites)
  - Format: `{sanitized_name}_assembly_manual.pdf`

---

## Technical Architecture

### Technology Stack

**Backend (Python)**
- **Framework:** FastAPI (async endpoints)
- **PDF Generation:** reportlab v4.0+ (native PDF rendering)
- **Image Processing:** Pillow v10.0+ (SVG to image if needed)
- **Data Access:** BaseRepository abstraction (in-memory, SQLite, or PostgreSQL)
- **Validation:** Pydantic schemas
- **Error Handling:** FastAPI exceptions + custom error classes
- **Logging:** Python logging module

**Frontend (Next.js/React)**
- **Trigger:** Export buttons in AssemblyPageContent and PartsPageContent
- **API Client:** Existing `exportAssemblyPDF()` in `services/api.ts`
- **State Management:** Component-level state (isExporting boolean)
- **UI Feedback:** Toast notifications (success/error), loading spinner
- **Download:** Blob API with dynamic filename

### Detailed Data Pipeline

#### PHASE 1: REQUEST VALIDATION
```
Frontend sends POST /api/v1/step/export-pdf
├─ Body: { "model_id": "550e8400-..." }
└─ Header: Content-Type: application/json

Backend validation:
├─ Validate UUID format (model_id)
├─ Check model_id is not empty/null
├─ Limit max request size (1KB)
└─ Return 400 Bad Request if invalid
```

#### PHASE 2: DATA RETRIEVAL (with error handling)
```
Backend fetches data from Repository:

1. Get Model Metadata
   ├─ Query: repository.get_model(model_id)
   ├─ Return: { id, file_name, file_size, created_at }
   └─ Error (404): Model not found → Return 404 "Model not found"

2. Get Parts List
   ├─ Query: repository.get_parts(model_id)
   ├─ Return: List[Part] with { id, type, quantity, dimensions }
   ├─ Validation: Handle empty list (no parts)
   └─ Error: Log warning, continue with warning in PDF

3. Get Assembly Steps
   ├─ Query: repository.get_assembly_steps(model_id)
   ├─ Return: List[AssemblyStep] with all metadata
   ├─ Validation: Handle empty list (no steps)
   ├─ Sort: By step_number ascending
   └─ Error: Log warning, continue with warning in PDF

4. Validate Retrieved Data
   ├─ At least one data type present (parts OR steps)
   └─ Return 404 if NO data at all
```

#### PHASE 3: DATA TRANSFORMATION
```
Transform raw data into PDF-friendly format:

1. Model Name Extraction
   ├─ Use file_name from model metadata
   ├─ Remove file extension (.step, .stp)
   ├─ Sanitize for filename (alphanumeric, dash, underscore only)
   ├─ Example: "table_base_assembly" from "table-base_assembly.step"
   └─ Fallback: Use first 8 chars of model_id if no file_name

2. Parts Grouping & Sorting
   ├─ Group by part_type (panel, hardware, fastener, structural, other)
   ├─ Sort each group by:
   │   ├─ Quantity (descending - most common first)
   │   └─ Dimension (largest first)
   ├─ Assign display order for table
   └─ Format dimensions: "{width}×{height}×{depth} mm"

3. Assembly Steps Normalization
   ├─ Validate all fields exist (default empty strings if not)
   ├─ Truncate long descriptions (max 500 chars)
   ├─ Validate SVG content (check for <svg> tag)
   ├─ Fallback: Use placeholder diagram if SVG invalid
   └─ Paginate if > 50 steps (split across multiple pages)

4. Statistics Calculation
   ├─ Total parts: Sum all quantities
   ├─ Total unique parts: Count distinct part_ids
   ├─ Assembly time: Sum of duration_minutes
   └─ Confidence average: Mean of confidence_scores (if LLM-generated)
```

#### PHASE 4: PDF GENERATION (with memory management)
```
Create PDF in memory with reportlab:

1. Initialize PDF Document
   ├─ Page size: A4 (210mm × 297mm)
   ├─ Margins: 20mm (all sides)
   ├─ Font setup: Helvetica, Times-Roman for rendering
   └─ Create BytesIO buffer for in-memory PDF

2. Render Cover Page
   ├─ Title: "Assembly Manual" (36pt, bold)
   ├─ Model name: From metadata (24pt, bold)
   ├─ Metadata table:
   │   ├─ Model ID: (8-char truncated UUID)
   │   ├─ Date: ISO format (YYYY-MM-DD)
   │   ├─ Total Parts: Count
   │   ├─ Total Steps: Count
   │   └─ Assembly Time: In hours/minutes
   ├─ Spacing: 12pt between sections
   └─ Page break after

3. Render Parts List Page(s)
   ├─ Heading: "Parts List" (20pt, bold)
   ├─ Table with columns:
   │   ├─ Part ID (10% width)
   │   ├─ Type (15% width)
   │   ├─ Quantity (10% width, right-aligned)
   │   ├─ Dimensions (35% width)
   │   └─ Volume (30% width)
   ├─ Table formatting:
   │   ├─ Header row: Gray background, bold text
   │   ├─ Alternating rows: White/light gray background
   │   ├─ Borders: 1pt black
   │   └─ Font: 9pt for data, 10pt for header
   ├─ Grouping: Visual separator between part type groups
   ├─ Pagination: If > 20 rows, split across pages
   └─ Footer: "Page X of Y"

4. Render Assembly Steps (1-per-page format)
   ├─ For each assembly step:
   │   ├─ Header: "Step {N} of {TOTAL}" (right-aligned, small)
   │   ├─ Title: Step title (18pt, bold, color: #333)
   │   ├─ Description: Main instruction (11pt, left-aligned)
   │   ├─ SVG Diagram:
   │   │   ├─ Embed exploded_view_svg if available (250mm width, max)
   │   │   ├─ Fallback: Render placeholder rectangle
   │   │   ├─ Wrap in frame with 1pt border
   │   │   └─ Error handling: Log SVG errors, use placeholder
   │   ├─ Part Callout Box (light gray background):
   │   │   ├─ List each part_indices with roles/names
   │   │   ├─ Include dimensions for clarity
   │   │   └─ Max 150 chars per line
   │   ├─ Assembly Sequence (if available):
   │   │   ├─ Format: "1. Align parts"
   │   │   ├─ "2. Insert fasteners"
   │   │   └─ Bullet points, 10pt font
   │   ├─ Tips/Warnings (if available):
   │   │   ├─ Tips: Green background, "💡 Tip:" prefix
   │   │   ├─ Warnings: Red background, "⚠️ Warning:" prefix
   │   │   └─ Font: 10pt, italic
   │   ├─ Spacing: 8pt between sections
   │   └─ Page break after (except last step)
   └─ Memory optimization: Generate in chunks, not all at once

5. Memory & Performance Handling
   ├─ Large PDFs (>50 steps):
   │   ├─ Estimate size before generation
   │   ├─ Warn in logs if > 10MB
   │   ├─ Stream generation in chunks (10 steps per batch)
   │   └─ Monitor memory usage
   ├─ SVG rendering:
   │   ├─ Cache SVG→Image conversions
   │   ├─ Limit max SVG file size (2MB)
   │   └─ Timeout SVG rendering (5 seconds)
   └─ Font loading: Use system fonts, fallback to Helvetica
```

#### PHASE 5: RESPONSE FORMATTING
```
Return PDF to Frontend:

1. Serialize PDF
   ├─ Get PDF bytes from BytesIO buffer
   ├─ Set content length
   └─ Calculate MD5 hash for integrity (optional)

2. Set HTTP Response Headers
   ├─ Content-Type: application/pdf
   ├─ Content-Disposition: attachment; filename="{model_name}_assembly_manual.pdf"
   ├─ Content-Length: {size in bytes}
   ├─ Cache-Control: no-cache, no-store, must-revalidate
   ├─ Pragma: no-cache
   ├─ Expires: 0
   └─ X-Content-Type-Options: nosniff

3. Return StreamingResponse
   ├─ Media type: "application/pdf"
   ├─ Filename: {sanitized_model_name}.pdf
   └─ Buffer mode: Chunk size 1MB
```

#### PHASE 6: ERROR HANDLING (Comprehensive)
```
Error scenarios and responses:

1. HTTP 400 - Bad Request
   └─ Reason: Invalid input (no model_id, wrong format)

2. HTTP 404 - Not Found
   └─ Reason: Model not found in database

3. HTTP 500 - Internal Server Error
   └─ Reasons:
      ├─ PDF generation exception
      ├─ SVG rendering crash
      ├─ Out of memory
      ├─ Repository connection error
      └─ Unknown exception

4. HTTP 503 - Service Unavailable
   └─ Reason: Repository temporarily unavailable

5. Timeout - 30 seconds max
   ├─ If PDF not generated within timeout
   ├─ Return 504 Gateway Timeout
   └─ Log timeout error

All errors logged with:
├─ Full stack trace
├─ Context (model_id, attempt number)
├─ Request details
└─ Timestamp
```

### Frontend Data Flow

```
┌─────────────────────────────────────┐
│ User clicks "PDF" button             │
│ (AssemblyPageContent or              │
│  PartsPageContent)                   │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Component calls exportAssemblyPDF()  │
│ (from services/api.ts)              │
│ ├─ Payload: { model_id }            │
│ └─ Response type: blob               │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Frontend State: isExporting = true   │
│ ├─ Show spinner                      │
│ └─ Disable button                    │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ API Request (Axios)                 │
│ POST /api/v1/step/export-pdf        │
│ Timeout: 30 seconds                 │
└────────────┬────────────────────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
   SUCCESS       ERROR/TIMEOUT
      │             │
      ▼             ▼
   Create        Show error
   Blob URL      toast
      │
      ▼
   Create <a>
   element
      │
      ▼
   Download
   file
      │
      ▼
   Show success
   toast
      │
      ▼
   Cleanup
```

---

## Implementation Tasks - DETAILED SPECIFICATIONS

### Phase 1: Backend Setup & Dependencies (4 hours)

#### Task 1.1: Install PDF Dependencies
**Objective:** Add all required Python packages for PDF generation

**Steps:**
1. Open `backend/pyproject.toml`
2. Locate `[dependencies]` section
3. Add the following packages:
   ```toml
   reportlab = "^4.0.0"          # PDF generation engine
   Pillow = "^10.0.0"            # Image processing (for SVG if needed)
   ```
4. Save file
5. Run `uv sync` to download and install
6. Verify installation: `uv run python -c "import reportlab; from PIL import Image; print('OK')"`

**Expected Output:**
```
OK
```

**Error Handling:**
- If `reportlab` install fails: Check for missing C dependencies, update uv
- If `Pillow` install fails: May need system libraries (libjpeg, libpng)

**Files Modified:**
- `backend/pyproject.toml`

**Verification Checklist:**
- [ ] reportlab v4.0+ installed
- [ ] Pillow v10.0+ installed
- [ ] Both packages importable in Python
- [ ] No version conflicts with existing packages

---

#### Task 1.2: Create PDF Generator Service
**Objective:** Build comprehensive PDF generation service with all rendering methods

**File to Create:** `backend/app/services/pdf_generator.py`

**Structure:**
```python
# ============================================================================
# IMPORTS
# ============================================================================
from io import BytesIO
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, pt
from reportlab.lib.colors import HexColor, grey, lightgrey, white
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak,
    Image, Frame, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from PIL import Image as PILImage

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

# Page dimensions (A4 in mm)
PAGE_WIDTH_MM = 210
PAGE_HEIGHT_MM = 297
MARGIN_MM = 20
MARGIN_PT = MARGIN_MM * mm

# Colors
COLOR_TITLE = HexColor("#1a1a1a")
COLOR_HEADING = HexColor("#333333")
COLOR_TEXT = HexColor("#4a4a4a")
COLOR_TABLE_HEADER = HexColor("#e8e8e8")
COLOR_WARNING = HexColor("#ffcccc")
COLOR_TIP = HexColor("#ccffcc")

# Font sizes
FONT_TITLE = 36
FONT_HEADING = 20
FONT_SUBHEADING = 18
FONT_BODY = 11
FONT_SMALL = 10
FONT_TINY = 9

# Spacing
SPACING_LARGE = 12 * mm
SPACING_MEDIUM = 8 * mm
SPACING_SMALL = 4 * mm


# ============================================================================
# PYDANTIC REQUEST/RESPONSE MODELS (for validation)
# ============================================================================

from pydantic import BaseModel

class PDFExportRequest(BaseModel):
    model_id: str
    # step_index: Optional[int] = None  # Currently unused (full manual only)


# ============================================================================
# PDF GENERATOR CLASS
# ============================================================================

class PDFGenerator:
    """
    Generates professional IKEA-style assembly instruction PDFs.
    
    Usage:
        generator = PDFGenerator()
        pdf_bytes = await generator.generate_assembly_manual(model_id, repository)
        # pdf_bytes can be returned as response blob
    """

    def __init__(self):
        self.page_width = PAGE_WIDTH_MM * mm
        self.page_height = PAGE_HEIGHT_MM * mm
        self.margin = MARGIN_PT
        self.content_width = self.page_width - (2 * self.margin)
        self.content_height = self.page_height - (2 * self.margin)
        
        # Cached styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self) -> None:
        """Configure custom paragraph styles for PDF rendering."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=FONT_TITLE,
            textColor=COLOR_TITLE,
            spaceAfter=SPACING_LARGE,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=FONT_HEADING,
            textColor=COLOR_HEADING,
            spaceAfter=SPACING_MEDIUM,
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=FONT_BODY,
            textColor=COLOR_TEXT,
            spaceAfter=SPACING_SMALL,
            alignment=TA_LEFT
        ))

    async def generate_assembly_manual(
        self,
        model_id: str,
        repository: Any,  # BaseRepository
        timeout_seconds: int = 30
    ) -> bytes:
        """
        Generate complete assembly manual PDF.
        
        Args:
            model_id: UUID of the model to export
            repository: Data repository (in-memory, SQLite, or PostgreSQL)
            timeout_seconds: Max time to wait for generation (default 30s)
        
        Returns:
            Binary PDF data (bytes)
        
        Raises:
            ValueError: If model not found or invalid
            Exception: If PDF generation fails
        """
        logger.info(f"Generating PDF for model: {model_id}")
        
        # Fetch data from repository
        model = await repository.get_model(model_id)
        if model is None:
            logger.error(f"Model not found: {model_id}")
            raise ValueError(f"Model {model_id} not found")
        
        parts = await repository.get_parts(model_id) or []
        steps = await repository.get_assembly_steps(model_id) or []
        
        # Validate we have at least some data
        if not parts and not steps:
            logger.error(f"No parts or steps for model: {model_id}")
            raise ValueError(f"No assembly data for model {model_id}")
        
        logger.info(f"Retrieved {len(parts)} parts and {len(steps)} steps")
        
        # Create in-memory PDF
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=A4,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        # Build story (list of elements to render)
        story = []
        
        try:
            # Add cover page
            story.extend(self._create_cover_page(model))
            story.append(PageBreak())
            
            # Add parts list (if parts exist)
            if parts:
                story.extend(self._create_parts_page(parts))
                story.append(PageBreak())
            else:
                logger.warning(f"No parts for model {model_id}")
                story.append(Paragraph(
                    "No parts data available for this assembly.",
                    self.styles['CustomBody']
                ))
                story.append(PageBreak())
            
            # Add assembly steps
            if steps:
                for i, step in enumerate(steps):
                    story.extend(self._create_assembly_step_page(step, i + 1, len(steps)))
                    if i < len(steps) - 1:  # Don't add page break after last step
                        story.append(PageBreak())
            else:
                logger.warning(f"No assembly steps for model {model_id}")
                story.append(Paragraph(
                    "No assembly instructions available for this model.",
                    self.styles['CustomBody']
                ))
            
            # Build PDF
            doc.build(story)
            
            # Get binary content
            pdf_bytes = pdf_buffer.getvalue()
            logger.info(f"PDF generated successfully: {len(pdf_bytes)} bytes")
            
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Failed to generate PDF: {str(e)}", exc_info=True)
            raise

    def _create_cover_page(self, model: Dict[str, Any]) -> List:
        """
        Generate cover page content.
        
        Args:
            model: Model metadata dict with keys: file_name, file_size, created_at
        
        Returns:
            List of reportlab elements for cover page
        """
        story = []
        
        # Title
        story.append(Paragraph("Assembly Manual", self.styles['CustomTitle']))
        story.append(Spacer(1, SPACING_LARGE))
        
        # Model name
        model_name = model.get('file_name', 'Unknown').replace('.step', '').replace('.stp', '')
        story.append(Paragraph(f"<b>{model_name}</b>", self.styles['CustomHeading']))
        story.append(Spacer(1, SPACING_MEDIUM))
        
        # Info table
        info_data = [
            ['Model ID:', model.get('id', 'N/A')[:8]],
            ['Generated:', datetime.now().strftime('%Y-%m-%d')],
        ]
        
        info_table = Table(info_data, colWidths=[60*mm, 80*mm])
        info_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', FONT_SMALL),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', FONT_SMALL),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        
        return story

    def _create_parts_page(self, parts: List[Dict[str, Any]]) -> List:
        """
        Generate parts list page content.
        
        Args:
            parts: List of part dicts with keys: id, part_type, quantity, dimensions
        
        Returns:
            List of reportlab elements for parts page
        """
        story = []
        
        # Heading
        story.append(Paragraph("Parts List", self.styles['CustomHeading']))
        story.append(Spacer(1, SPACING_SMALL))
        
        # Sort and group parts
        grouped = self._group_parts(parts)
        
        # Build table
        table_data = [['Part ID', 'Type', 'Qty', 'Dimensions (mm)']]
        
        for group_type, group_parts in grouped:
            for part in group_parts:
                dims = part.get('dimensions', {})
                dim_str = f"{dims.get('width', 0):.0f}×{dims.get('height', 0):.0f}×{dims.get('depth', 0):.0f}"
                
                table_data.append([
                    part.get('id', '?'),
                    group_type.capitalize(),
                    str(part.get('quantity', 1)),
                    dim_str
                ])
        
        # Create table with styling
        table = Table(table_data, colWidths=[30*mm, 40*mm, 20*mm, 70*mm])
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_TABLE_HEADER),
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', FONT_SMALL),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            
            # Data rows
            ('FONT', (0, 1), (-1, -1), 'Helvetica', FONT_TINY),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Qty column centered
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, lightgrey]),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#cccccc')),
        ]))
        
        story.append(table)
        return story

    def _create_assembly_step_page(
        self,
        step: Dict[str, Any],
        step_num: int,
        total_steps: int
    ) -> List:
        """
        Generate single assembly step page content.
        
        Args:
            step: Assembly step dict with keys: title, description, part_indices, etc.
            step_num: Current step number (1-indexed)
            total_steps: Total number of steps
        
        Returns:
            List of reportlab elements for step page
        """
        story = []
        
        # Step header
        header = f"Step {step_num} of {total_steps}"
        story.append(Paragraph(f"<font size='8' color='gray'>{header}</font>", self.styles['Normal']))
        story.append(Spacer(1, SPACING_SMALL))
        
        # Title
        title = step.get('title', 'Assembly Step')
        story.append(Paragraph(title, self.styles['CustomSubheading']))
        story.append(Spacer(1, SPACING_SMALL))
        
        # Description
        description = step.get('description', '')
        if description:
            story.append(Paragraph(description, self.styles['CustomBody']))
            story.append(Spacer(1, SPACING_SMALL))
        
        # SVG diagram (if available)
        svg_content = step.get('exploded_view_svg') or step.get('svg_diagram') or ''
        if svg_content:
            try:
                # Try to embed SVG (reportlab has some SVG support)
                # For complex SVGs, may need to convert to image first
                diagram_height = 80 * mm
                story.append(Paragraph("<b>Assembly Diagram:</b>", self.styles['Normal']))
                story.append(Spacer(1, SPACING_SMALL))
                # Note: SVG embedding depends on reportlab version and complexity
                # For now, add placeholder
                story.append(Paragraph(
                    "[Diagram would be embedded here]",
                    self.styles['Normal']
                ))
                story.append(Spacer(1, SPACING_SMALL))
            except Exception as e:
                logger.warning(f"Failed to embed SVG for step {step_num}: {e}")
        
        # Parts involved
        part_indices = step.get('part_indices', [])
        part_roles = step.get('part_roles', {})
        if part_indices:
            story.append(Paragraph("<b>Parts Involved:</b>", self.styles['Normal']))
            for idx in part_indices:
                role = part_roles.get(str(idx), f"Part {idx}")
                story.append(Paragraph(f"• {role}", self.styles['CustomBody']))
            story.append(Spacer(1, SPACING_SMALL))
        
        # Assembly sequence (if available)
        sequence = step.get('assembly_sequence', [])
        if sequence:
            story.append(Paragraph("<b>Steps:</b>", self.styles['Normal']))
            for i, seq_step in enumerate(sequence, 1):
                story.append(Paragraph(f"{i}. {seq_step}", self.styles['CustomBody']))
            story.append(Spacer(1, SPACING_SMALL))
        
        # Warnings
        warnings = step.get('warnings', [])
        if warnings:
            for warning in warnings:
                warning_style = ParagraphStyle(
                    'Warning',
                    parent=self.styles['Normal'],
                    fontSize=FONT_SMALL,
                    textColor=HexColor('#cc0000'),
                    backColor=COLOR_WARNING
                )
                story.append(Paragraph(f"⚠️ <b>Warning:</b> {warning}", warning_style))
            story.append(Spacer(1, SPACING_SMALL))
        
        # Tips
        tips = step.get('tips', [])
        if tips:
            for tip in tips:
                tip_style = ParagraphStyle(
                    'Tip',
                    parent=self.styles['Normal'],
                    fontSize=FONT_SMALL,
                    textColor=HexColor('#006600'),
                    backColor=COLOR_TIP
                )
                story.append(Paragraph(f"💡 <b>Tip:</b> {tip}", tip_style))
        
        return story

    def _group_parts(self, parts: List[Dict[str, Any]]) -> List[tuple]:
        """
        Group parts by type and sort.
        
        Args:
            parts: List of part dicts
        
        Returns:
            List of tuples: [(part_type, [parts])]
        """
        groups = {}
        for part in parts:
            part_type = part.get('part_type', 'other')
            if part_type not in groups:
                groups[part_type] = []
            groups[part_type].append(part)
        
        # Sort groups by type priority and parts by quantity
        type_priority = ['panel', 'structural', 'hardware', 'fastener', 'other']
        result = []
        for pt in type_priority:
            if pt in groups:
                sorted_parts = sorted(
                    groups[pt],
                    key=lambda p: p.get('quantity', 0),
                    reverse=True
                )
                result.append((pt, sorted_parts))
        
        return result
```

**Testing:**
- Instantiate `PDFGenerator()`
- Call all methods with sample data
- Verify no import errors

**Files Created:**
- `backend/app/services/pdf_generator.py`

**Acceptance Criteria:**
- [ ] PDFGenerator class instantiates without errors
- [ ] All methods have proper signatures
- [ ] Docstrings complete for all public methods
- [ ] Custom styles configured correctly
- [ ] No syntax errors

---

#### Task 1.3: Create PDF Export Endpoint
**Objective:** Create FastAPI endpoint for PDF export

**File to Create:** `backend/app/api/v1/endpoints/pdf.py`

**Content Structure:**
```python
"""PDF export endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse

from app.container import ServiceContainer, get_container
from app.models.schemas import PDFExportRequest
from app.services.pdf_generator import PDFGenerator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/step/export-pdf")
async def export_assembly_pdf(
    request: PDFExportRequest,
    container: ServiceContainer = Depends(get_container),
    user_agent: Annotated[str | None, Header()] = None,
) -> StreamingResponse:
    """
    Export assembly manual as PDF.
    
    Generates a professional IKEA-style PDF with:
    - Cover page with model info
    - Parts list
    - Step-by-step assembly instructions with diagrams
    
    Args:
        request: { "model_id": "uuid" }
        container: Service container with repository access
        user_agent: Browser user agent (for logging)
    
    Returns:
        StreamingResponse with binary PDF blob
    
    Raises:
        HTTPException: 400 if request invalid
        HTTPException: 404 if model not found
        HTTPException: 500 if generation fails
        HTTPException: 503 if database unavailable
    
    Example:
        POST /api/v1/step/export-pdf
        Content-Type: application/json
        {"model_id": "550e8400-e29b-41d4-a716-446655440000"}
        
        Response:
        200 OK
        Content-Type: application/pdf
        Content-Disposition: attachment; filename="model_assembly_manual.pdf"
        [Binary PDF Data]
    """
    
    try:
        # Validate request
        if not request.model_id:
            logger.warning("Export request missing model_id")
            raise HTTPException(status_code=400, detail="model_id is required")
        
        # Get repository
        repository = await container.get_repository()
        
        # Generate PDF
        pdf_generator = PDFGenerator()
        try:
            pdf_bytes = await pdf_generator.generate_assembly_manual(
                request.model_id,
                repository,
                timeout_seconds=30
            )
        except ValueError as e:
            logger.error(f"PDF generation validation error: {str(e)}")
            raise HTTPException(status_code=404, detail=str(e))
        except TimeoutError:
            logger.error(f"PDF generation timeout for model {request.model_id}")
            raise HTTPException(status_code=504, detail="PDF generation timeout")
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to generate PDF")
        
        # Generate filename
        model = await repository.get_model(request.model_id)
        filename = self._sanitize_filename(model.get('file_name', 'assembly'))
        
        # Return PDF as streaming response
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}_assembly_manual.pdf"',
                "Content-Length": str(len(pdf_bytes)),
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "X-Content-Type-Options": "nosniff",
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in export endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@staticmethod
def _sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe download.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename with extension removed
    """
    import re
    # Remove file extension
    base = filename.rsplit('.', 1)[0] if '.' in filename else filename
    # Keep only alphanumeric, dash, underscore
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', base)
    # Limit length
    return sanitized[:100] if sanitized else "assembly"
```

**Update Imports:**
- In `backend/app/api/v1/__init__.py`, add PDF router to imports

**File Modifications:**
- `backend/app/api/v1/endpoints/pdf.py` - CREATE
- `backend/app/api/v1/__init__.py` - UPDATE (add router import)
- `backend/app/models/schemas.py` - UPDATE (add PDFExportRequest model if not exists)

**Acceptance Criteria:**
- [ ] Endpoint receives POST requests
- [ ] Validates model_id
- [ ] Calls PDFGenerator
- [ ] Returns PDF with correct headers
- [ ] Handles errors gracefully
- [ ] Returns correct HTTP status codes

---

### Phase 2: Frontend Integration (3 hours)

#### Task 2.1: Implement PDF Export Functions
- [ ] Update `frontend/components/custom/AssemblyPageContent.tsx`
  - Replace `handleExportFullPDF()` alert with actual export logic
  - Add loading state and error handling
  - Show success/error toast

- [ ] Update `frontend/components/custom/PartsPageContent.tsx`
  - Replace `handleExportPDF()` alert with actual export logic
  - Add loading state and error handling

**Implementation Pattern:**

```typescript
const handleExportFullPDF = async () => {
  setIsExporting(true);
  try {
    const blob = await exportAssemblyPDF(modelId);
    
    // Create download link
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${modelName}_assembly_manual.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showSuccessToast("PDF downloaded successfully");
  } catch (error) {
    showErrorToast("Failed to export PDF: " + error.message);
  } finally {
    setIsExporting(false);
  }
};
```

**Files Modified:**
- `frontend/components/custom/AssemblyPageContent.tsx`
- `frontend/components/custom/PartsPageContent.tsx`

**Acceptance:** Buttons trigger actual PDF download with proper error handling

---

#### Task 2.2: Add Loading States & UI Feedback
- [ ] Add loading spinner while PDF generates
- [ ] Add success toast notification
- [ ] Add error toast notification
- [ ] Disable button while exporting

**Files Modified:**
- `frontend/components/custom/AssemblyPageContent.tsx`
- `frontend/components/custom/PartsPageContent.tsx`

**Acceptance:** User sees feedback during export process

---

### Phase 3: Testing & Refinement (3 hours)

#### Task 3.1: Backend Testing
- [ ] Test PDF generation with sample assembly data
- [ ] Verify PDF structure and content
- [ ] Test error cases:
  - Invalid model_id
  - Missing parts data
  - Missing assembly steps
- [ ] Test large PDFs (many steps)

**Test Coverage:**
- ✅ Happy path: Valid model generates complete PDF
- ✅ Edge case: Model with no parts
- ✅ Edge case: Model with single step
- ✅ Error case: Non-existent model returns 404

**Files Created:**
- `backend/tests/test_pdf_export.py`

**Acceptance:** All tests pass

---

#### Task 3.2: Frontend Testing
- [ ] Test export button click flow
- [ ] Test download triggers correctly
- [ ] Test error handling and user feedback
- [ ] Test with various model sizes

**Manual Tests:**
- ✅ Click export → PDF downloads with correct filename
- ✅ Large PDF generates without timeout
- ✅ Network error shows error toast
- ✅ Success shows success toast

**Acceptance:** All manual tests pass

---

#### Task 3.3: Integration Testing
- [ ] End-to-end flow: Upload → Export → Verify PDF
- [ ] Check PDF opens correctly in PDF reader
- [ ] Verify content accuracy (steps, parts, diagrams)
- [ ] Test cross-browser download

**Acceptance:** PDF is valid, readable, and contains all expected content

---

### Phase 4: Documentation & Deployment (2 hours)

#### Task 4.1: Code Documentation
- [ ] Add JSDoc comments to frontend functions
- [ ] Add docstrings to backend service methods
- [ ] Add comments for complex logic (SVG rendering, layout calculations)

**Files Modified:**
- `backend/app/services/pdf_generator.py`
- `backend/app/api/v1/endpoints/pdf.py`
- `frontend/components/custom/AssemblyPageContent.tsx`
- `frontend/components/custom/PartsPageContent.tsx`

**Acceptance:** All public functions documented

---

#### Task 4.2: Environment & Dependencies
- [ ] Update `.env.example` with any new variables (if needed)
- [ ] Add installation instructions to README
- [ ] Update project requirements documentation

**Files Modified:**
- `backend/.env.example` (if needed)
- `backend/README.md`
- `IMPLEMENTATION_PLAN.md` (this file)

**Acceptance:** Documentation is complete and clear

---

#### Task 4.3: Branch Cleanup & PR Preparation
- [ ] Verify all tests pass
- [ ] Check code formatting and linting
- [ ] Create summary of changes
- [ ] Prepare for merge to master

**Acceptance:** Branch ready for code review and merge

---

## Data Structures & APIs

### Request/Response

#### Export PDF Endpoint

**Request:**
```http
POST /api/v1/step/export-pdf
Content-Type: application/json

{
  "model_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (Success):**
```http
200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="table_assembly_manual.pdf"
Content-Length: 245623

[Binary PDF Data]
```

**Response (Error):**
```http
404 Not Found
Content-Type: application/json

{
  "detail": "Model not found"
}
```

---

### PDF Page Structure

**Page 1: Cover Page**
- Title: "Assembly Manual"
- Model Name: From metadata
- Model ID: For reference
- Total Parts: Count
- Total Steps: Count
- Generated Date: ISO format
- Footer: WEBLE logo/branding

**Page 2: Parts List**
- Table with columns:
  - Part ID (A, B, C, etc.)
  - Part Type (Panel, Hardware, etc.)
  - Quantity (×n)
  - Dimensions (W × H × D mm)
  - Material/Classification
- Grouped and sorted by type
- Illustrations: Small thumbnails if available

**Pages 3-N: Assembly Steps**
- Each step on one page
- Header: "Step 1", "Step 2", etc.
- Title: Step title (e.g., "Assemble Left Panel")
- Description: Full step instructions
- Diagram: SVG showing parts involved
- Parts Callout: List of parts used with labels
- Tip/Warning box if applicable
- Footer: Step number, page number

**Last Page: Back Cover**
- Optional: Customer support info, contact details
- QR code for digital manual (if applicable)

---

## Dependencies to Install

### Backend (Python)

```
reportlab>=4.0.0          # PDF generation
Pillow>=10.0.0            # Image/SVG handling
```

Add to `backend/pyproject.toml`:
```toml
[dependencies]
reportlab = "^4.0.0"
Pillow = "^10.0.0"
```

---

## Potential Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| SVG rendering in PDF | Use reportlab's SVG support or convert to image first |
| Layout precision | Use reportlab's positioning, not CSS |
| Unicode/Font support | Use reportlab's Unicode fonts or embedded fonts |
| Large PDFs (100+ steps) | Stream generation, pagination, consider splitting |
| Performance | Cache generated PDFs briefly if model doesn't change |
| Memory usage | Generate incrementally, use streaming if possible |

---

## File Checklist

### Backend Files to Create
- [ ] `backend/app/services/pdf_generator.py` - Main PDF generation logic
- [ ] `backend/app/api/v1/endpoints/pdf.py` - API endpoint
- [ ] `backend/tests/test_pdf_export.py` - Unit tests

### Backend Files to Modify
- [ ] `backend/pyproject.toml` - Add reportlab, Pillow
- [ ] `backend/app/api/v1/__init__.py` - Import pdf router
- [ ] `backend/app/api/v1/endpoints/__init__.py` - Export pdf router
- [ ] `backend/README.md` - Update documentation

### Frontend Files to Modify
- [ ] `frontend/components/custom/AssemblyPageContent.tsx` - Implement export
- [ ] `frontend/components/custom/PartsPageContent.tsx` - Implement export

---

## Success Criteria

✅ All acceptance criteria met:
- PDF generation works end-to-end
- All required pages included (cover, parts, assembly steps)
- IKEA-style professional layout
- Backend efficiently generates PDFs
- Frontend properly handles download and errors
- Tests all passing (unit, integration, manual)
- No performance degradation
- Code is well-documented

✅ Branch ready to merge to master

---

## Timeline Estimate

| Phase | Tasks | Estimated Hours | Status |
|-------|-------|-----------------|--------|
| Phase 1 | Backend Setup | 4 | 🔄 Pending |
| Phase 2 | Frontend Integration | 3 | ⏳ Pending |
| Phase 3 | Testing & Refinement | 3 | ⏳ Pending |
| Phase 4 | Documentation | 2 | ⏳ Pending |
| **Total** | | **12 hours** | **Planning** |

---

### Phase 2: Frontend Integration (3 hours)

#### Task 2.1: Implement Assembly PDF Export
**Objective:** Replace alert() in AssemblyPageContent with actual export logic

**File to Modify:** `frontend/components/custom/AssemblyPageContent.tsx`

**Changes Required:**
1. Add import for `exportAssemblyPDF` from api service (already exists)
2. Add state variables for export status
3. Replace `handleExportFullPDF` function with actual implementation
4. Add loading UI and error handling

**Code to Add:**
```typescript
// Add to imports
import { useToast } from "@/hooks/use-toast";  // For success/error notifications

// Add state inside component
const [isExporting, setIsExporting] = useState(false);
const { toast } = useToast();

// Replace handleExportFullPDF function
const handleExportFullPDF = async () => {
  if (!steps || steps.length === 0) {
    toast({
      title: "Brak instrukcji",
      description: "Brak instrukcji montażu do eksportu",
      variant: "destructive"
    });
    return;
  }

  setIsExporting(true);
  try {
    const blob = await exportAssemblyPDF(modelId);
    
    // Create object URL
    const url = URL.createObjectURL(blob);
    
    // Create download link
    const link = document.createElement("a");
    link.href = url;
    link.download = `assembly_manual_${new Date().getTime()}.pdf`;
    
    // Trigger download
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Cleanup
    URL.revokeObjectURL(url);
    
    toast({
      title: "Sukces",
      description: "Instrukcja została pobrana",
      variant: "default"
    });
  } catch (error) {
    console.error("PDF export failed:", error);
    toast({
      title: "Błąd",
      description: error instanceof Error ? error.message : "Nie udało się eksportować PDF",
      variant: "destructive"
    });
  } finally {
    setIsExporting(false);
  }
};

// Update button styling to show loading state
// In the render section, update the button:
<Button
  onClick={handleExportFullPDF}
  disabled={isExporting || !steps || steps.length === 0}
  className="h-9 px-4 bg-lilac_ash-400 hover:bg-lilac_ash-500 text-charcoal-800 font-semibold rounded-2xl transition-colors"
>
  <span className="flex items-center gap-2">
    {isExporting ? (
      <>
        <span className="animate-spin">⟳</span>
        Generowanie...
      </>
    ) : (
      <>
        <Download className="w-4 h-4" />
        PDF Wszystkie
      </>
    )}
  </span>
</Button>
```

**Files Modified:**
- `frontend/components/custom/AssemblyPageContent.tsx`

**Acceptance Criteria:**
- [ ] Export button triggers actual export
- [ ] Loading state shows spinner
- [ ] Button disabled while exporting
- [ ] Success toast shows on success
- [ ] Error toast shows on failure
- [ ] File downloads with correct name

---

#### Task 2.2: Implement Parts PDF Export
**Objective:** Implement export in PartsPageContent

**File to Modify:** `frontend/components/custom/PartsPageContent.tsx`

**Changes Required:**
Same pattern as Assembly page, but for parts list

**Code Pattern:**
```typescript
// Similar to assembly export, but:
// - Check for parts.length > 0
// - Use same exportAssemblyPDF function (backend handles both)
// - Download filename: `parts_list_{timestamp}.pdf`
```

**Files Modified:**
- `frontend/components/custom/PartsPageContent.tsx`

**Acceptance Criteria:**
- [ ] Parts export button functional
- [ ] Proper error handling
- [ ] Loading state visible
- [ ] File downloads

---

#### Task 2.3: Add Toast Notifications Utilities
**Objective:** Ensure toast notifications work correctly

**Verification:**
- [ ] Check if `@/hooks/use-toast` exists in project
- [ ] If not, implement or use alternative notification library
- [ ] Test toast rendering

**Files to Check:**
- `frontend/hooks/use-toast.ts` (should exist if using shadcn/ui)

---

### Phase 3: Testing & Validation (3 hours)

#### Task 3.1: Backend Integration Tests
**Objective:** Test PDF generation end-to-end

**File to Create:** `backend/tests/test_pdf_export.py`

**Test Cases:**
```python
# Test 1: Successful PDF generation
async def test_export_valid_model():
    # Setup: Create test model with parts and steps
    # Call: POST /api/v1/step/export-pdf
    # Assert: Status 200, Content-Type application/pdf, PDF is valid

# Test 2: Missing model returns 404
async def test_export_missing_model():
    # Call: POST /api/v1/step/export-pdf with invalid model_id
    # Assert: Status 404

# Test 3: Invalid request returns 400
async def test_export_invalid_request():
    # Call: POST /api/v1/step/export-pdf with no model_id
    # Assert: Status 400

# Test 4: Empty parts/steps handled gracefully
async def test_export_empty_data():
    # Setup: Model with no parts or steps
    # Call: POST /api/v1/step/export-pdf
    # Assert: Status 200, PDF with warning messages

# Test 5: Large PDF (many steps)
async def test_export_large_assembly():
    # Setup: Model with 50+ assembly steps
    # Call: POST /api/v1/step/export-pdf
    # Assert: Status 200, reasonable response time (<5 seconds)
```

**Files Created:**
- `backend/tests/test_pdf_export.py`

**Verification:**
- [ ] All tests pass
- [ ] No timeout errors
- [ ] PDF files valid and readable

---

#### Task 3.2: Frontend Component Tests
**Objective:** Test export buttons and state management

**Manual Tests:**
1. **Test Export Flow:**
   - Navigate to Assembly page
   - Click "PDF Wszystkie" button
   - Observe: Spinner shows
   - Observe: Button disabled
   - Observe: File downloads
   - Observe: Success toast appears

2. **Test Error Handling:**
   - Simulate API error (network offline)
   - Click export
   - Observe: Error toast shows

3. **Test Edge Cases:**
   - Empty assembly (0 steps) - button disabled
   - Missing data - error handling
   - Large PDF - verify progress feedback

**Files Modified:**
- `frontend/components/custom/AssemblyPageContent.tsx`
- `frontend/components/custom/PartsPageContent.tsx`

**Acceptance Criteria:**
- [ ] Button click triggers export
- [ ] Loading state visible
- [ ] File downloads with correct name
- [ ] Toast notifications appear
- [ ] Error handling works

---

#### Task 3.3: End-to-End Integration Test
**Objective:** Full workflow test from upload to PDF export

**Test Steps:**
1. Upload STEP file
2. Wait for processing complete
3. Navigate to Assembly page
4. Click export button
5. Verify PDF downloads
6. Open PDF and check content:
   - [ ] Cover page present
   - [ ] Parts list accurate
   - [ ] All assembly steps included
   - [ ] Formatting professional
   - [ ] Diagrams embedded (or placeholder)

**Acceptance Criteria:**
- [ ] E2E flow works without errors
- [ ] PDF content is accurate and complete
- [ ] Timestamps match generated date
- [ ] File size reasonable (10MB max for reasonable assembly)

---

### Phase 4: Documentation & Deployment (2 hours)

#### Task 4.1: Code Documentation
**Objective:** Add comprehensive code comments

**Files to Document:**
1. `backend/app/services/pdf_generator.py`
   - [ ] Class docstring explaining PDF generation
   - [ ] Method docstrings with Args, Returns, Raises
   - [ ] Complex logic comments (grouping, styling, etc.)

2. `backend/app/api/v1/endpoints/pdf.py`
   - [ ] Endpoint docstring with usage example
   - [ ] Parameter descriptions
   - [ ] Error response documentation

3. `frontend/components/custom/AssemblyPageContent.tsx`
   - [ ] Comment explaining export flow
   - [ ] Toast notification logic

4. `frontend/components/custom/PartsPageContent.tsx`
   - [ ] Similar frontend documentation

---

#### Task 4.2: Update Project Documentation
**Objective:** Document feature in project files

**Files to Update:**
1. `backend/README.md`
   - Add section: "PDF Export Feature"
   - Document new endpoint: `POST /api/v1/step/export-pdf`
   - Example request/response

2. `ARCHITECTURE.md`
   - Update frontend components section
   - Add PDF Generator to backend services

3. `PDF_EXPORT_IMPLEMENTATION_PLAN.md`
   - Mark as completed
   - Add implementation notes

---

#### Task 4.3: Final Quality Assurance
**Objective:** Ensure production readiness

**Checklist:**
- [ ] All tests passing
- [ ] No console errors or warnings
- [ ] Code follows project style guide
- [ ] Error messages are user-friendly (Polish)
- [ ] Performance acceptable (<5s for reasonable PDF)
- [ ] Security: No SQL injection, file traversal, etc.
- [ ] Browser compatibility: Chrome, Firefox, Safari, Edge
- [ ] Mobile responsive (if applicable)
- [ ] Accessibility: Proper button labels, ARIA attributes

**Final Verification:**
- [ ] Run linter: `uv run ruff check app/`
- [ ] Run formatter: `uv run black app/`
- [ ] Run tests: `uv run pytest tests/`
- [ ] Manual smoke test: Upload → Export → Verify PDF

---

## Edge Cases & Error Scenarios

### Backend Edge Cases

| Scenario | Handling | HTTP Status |
|----------|----------|-------------|
| Model doesn't exist | Log error, return error message | 404 |
| No parts or steps data | Generate PDF with warning message | 200 (partial) |
| Invalid SVG diagram | Fallback to placeholder diagram | 200 (with note) |
| PDF > 10MB | Log warning, continue generation | 200 |
| Timeout (>30s) | Abort generation, return error | 504 |
| Out of memory | Log error, return 500 | 500 |
| Repository unavailable | Return 503 | 503 |
| Malformed request body | Return 400 | 400 |

### Frontend Edge Cases

| Scenario | Handling |
|----------|----------|
| Network error | Toast error, retry button |
| Export timeout (>30s) | Cancel download, show error |
| Large PDF (>100MB) | Warn user, proceed or cancel |
| Browser doesn't support Blob API | Fallback message |
| Multiple clicks | Debounce, prevent duplicate requests |

---

## Performance Considerations

### Memory Usage
- **Target:** < 100MB for typical assembly (50 steps)
- **Max PDF:** 10MB uncompressed
- **Strategy:** Stream generation in chunks, use BytesIO

### Generation Time
- **Target:** < 5 seconds for typical assembly
- **Benchmark:** 1 step per 50ms
- **Optimization:** Parallel rendering, caching

### Network
- **Compression:** No compression (already binary)
- **Chunking:** Stream in 1MB chunks
- **Timeout:** 30 seconds client-side

---

## Security Considerations

1. **Input Validation**
   - Validate UUID format for model_id
   - Sanitize filenames
   - Limit request size

2. **Output Encoding**
   - PDF properly encoded
   - Headers set correctly (no injection)
   - Filename sanitized

3. **Data Access**
   - Only return data for the requested model
   - Use repository access control
   - Log all exports for audit trail

4. **Resource Limits**
   - Max PDF size: 100MB
   - Max generation time: 30 seconds
   - Rate limit: TBD (depends on deployment)

---

## Deployment Notes

### Environment Requirements
- **Python:** 3.10+
- **reportlab:** 4.0+
- **Pillow:** 10.0+
- **Memory:** ≥ 512MB for PDF generation
- **Disk:** ≥ 1GB temporary space

### Configuration
No new environment variables needed (uses existing settings)

### Monitoring
- Track PDF export count (metrics)
- Monitor generation time (performance)
- Log all errors (debugging)
- Alert on timeout/failure rate

---

## Next Steps

1. ✅ Create feat/pdf branch (DONE)
2. ✅ Create comprehensive implementation plan (DONE)
3. ⏳ Begin Phase 1: Backend Setup
4. ⏳ Begin Phase 2: Frontend Integration
5. ⏳ Conduct Phase 3: Testing
6. ⏳ Complete Phase 4: Documentation
7. ⏳ Create Pull Request for review
8. ⏳ Merge to master after review

---

**Branch:** `feat/pdf`  
**Created:** 2026-04-26  
**Last Updated:** 2026-04-26  
**Status:** ✅ DETAILED SPECIFICATION COMPLETE - READY FOR IMPLEMENTATION
