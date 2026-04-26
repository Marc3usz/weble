"""PDF Export Service - Generates professional assembly instruction PDFs."""

import io
import logging
from datetime import datetime
from typing import List, Optional, Tuple
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
    Image,
    KeepTogether,
)
from reportlab.pdfgen import canvas
from PIL import Image as PILImage
import base64

from app.models.schemas import AssemblyStep, Part, SvgDrawing
from app.services.step_loader import PipelineStage

logger = logging.getLogger(__name__)


class PDFGeneratorService(PipelineStage):
    """
    Generate professional IKEA-style assembly instruction PDFs.

    Features:
    - Title page with model metadata
    - Parts list with specifications
    - Step-by-step assembly instructions
    - Technical drawings and 3D diagrams
    - Professional formatting and styling
    """

    def __init__(self) -> None:
        """Initialize PDF generator service."""
        self.name = "PDFGeneratorService"
        self.logger = logging.getLogger(__name__)
        self.page_width, self.page_height = letter
        self.margin = 0.5 * inch

    async def validate_input(self, data: dict) -> bool:
        """
        Validate PDF generation input parameters.

        Args:
            data: Dictionary containing PDF generation parameters

        Returns:
            True if input is valid, False otherwise
        """
        if not isinstance(data, dict):
            return False

        # Check required fields
        if not isinstance(data.get("parts"), list):
            return False

        if not isinstance(data.get("assembly_steps"), list):
            return False

        if not data.get("model_name") or not isinstance(data["model_name"], str):
            return False

        if not data.get("filename") or not isinstance(data["filename"], str):
            return False

        # SVG drawings can be empty, but should be a list if present
        if "svg_drawings" in data and not isinstance(data.get("svg_drawings"), list):
            return False

        return True

    async def generate_assembly_pdf(
        self,
        filename: str,
        model_name: str,
        parts: List[Part],
        svg_drawings: List[SvgDrawing],
        assembly_steps: List[AssemblyStep],
        parts_2d_svgs: Optional[List[SvgDrawing]] = None,
    ) -> bytes:
        """
        Generate a complete assembly instruction PDF.

        Args:
            filename: Original filename for metadata
            model_name: Name of the model/furniture
            parts: List of extracted parts
            svg_drawings: SVG diagrams for parts
            assembly_steps: Assembly instruction steps
            parts_2d_svgs: Optional 2D technical drawings for each part

        Returns:
            PDF file as bytes
        """
        logger.info(f"Generating PDF for model: {model_name}")

        # Create PDF document in memory
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin,
        )

        # Build document content
        elements = []

        # 1. Title Page
        elements.extend(self._create_title_page(model_name, filename, len(assembly_steps)))
        elements.append(PageBreak())

        # 2. Parts List
        if parts:
            elements.extend(self._create_parts_list_page(parts, svg_drawings))
            elements.append(PageBreak())

        # 3. Assembly Instructions
        if assembly_steps:
            elements.extend(
                self._create_assembly_instructions_pages(assembly_steps, svg_drawings)
            )

        # Build PDF
        doc.build(elements)

        # Get PDF bytes
        pdf_bytes = pdf_buffer.getvalue()
        logger.info(f"PDF generated successfully: {len(pdf_bytes)} bytes")

        return pdf_bytes

    def _create_title_page(
        self, model_name: str, filename: str, num_steps: int
    ) -> List:
        """Create title page for the PDF."""
        elements = []
        styles = getSampleStyleSheet()

        # Add spacing
        elements.append(Spacer(1, 1.5 * inch))

        # Title
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=36,
            textColor=colors.HexColor("#1a1a1a"),
            spaceAfter=30,
            alignment=1,  # Center
        )
        elements.append(Paragraph(model_name, title_style))

        # Subtitle
        elements.append(Spacer(1, 0.3 * inch))
        subtitle_style = ParagraphStyle(
            "Subtitle",
            parent=styles["Normal"],
            fontSize=14,
            textColor=colors.HexColor("#666666"),
            spaceAfter=20,
            alignment=1,
        )
        elements.append(Paragraph("Assembly Instructions", subtitle_style))

        # Metadata
        elements.append(Spacer(1, 0.5 * inch))
        metadata_style = ParagraphStyle(
            "Metadata",
            parent=styles["Normal"],
            fontSize=11,
            textColor=colors.HexColor("#999999"),
            spaceAfter=10,
            alignment=1,
        )

        now = datetime.now().strftime("%B %d, %Y")
        elements.append(Paragraph(f"Generated: {now}", metadata_style))
        elements.append(Paragraph(f"Total Steps: {num_steps}", metadata_style))
        elements.append(Paragraph(f"File: {filename}", metadata_style))

        return elements

    def _create_parts_list_page(
        self, parts: List[Part], svg_drawings: List[SvgDrawing]
    ) -> List:
        """Create parts list page with specifications."""
        elements = []
        styles = getSampleStyleSheet()

        # Header
        header_style = ParagraphStyle(
            "PageHeader",
            parent=styles["Heading2"],
            fontSize=20,
            textColor=colors.HexColor("#1a1a1a"),
            spaceAfter=20,
        )
        elements.append(Paragraph("Parts List", header_style))

        # Create parts table
        table_data = [
            [
                Paragraph("<b>Part ID</b>", styles["Normal"]),
                Paragraph("<b>Type</b>", styles["Normal"]),
                Paragraph("<b>Qty</b>", styles["Normal"]),
                Paragraph("<b>Volume (cm³)</b>", styles["Normal"]),
                Paragraph("<b>Dimensions</b>", styles["Normal"]),
            ]
        ]

        for part in parts:
            dims_str = f"W:{part.dimensions.get('width', 0):.1f} × H:{part.dimensions.get('height', 0):.1f} × D:{part.dimensions.get('depth', 0):.1f}"
            table_data.append(
                [
                    Paragraph(part.id, styles["Normal"]),
                    Paragraph(part.part_type.value.capitalize(), styles["Normal"]),
                    Paragraph(str(part.quantity), styles["Normal"]),
                    Paragraph(f"{part.volume:.2f}", styles["Normal"]),
                    Paragraph(dims_str, styles["Normal"]),
                ]
            )

        # Style the table
        table = Table(table_data, colWidths=[0.8 * inch, 1.2 * inch, 0.6 * inch, 1.2 * inch, 2 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _create_assembly_instructions_pages(
        self, assembly_steps: List[AssemblyStep], svg_drawings: List[SvgDrawing]
    ) -> List:
        """Create assembly instruction pages with step-by-step diagrams."""
        elements = []
        styles = getSampleStyleSheet()

        for i, step in enumerate(assembly_steps, 1):
            # Step header
            step_header_style = ParagraphStyle(
                "StepHeader",
                parent=styles["Heading2"],
                fontSize=16,
                textColor=colors.HexColor("#1a1a1a"),
                spaceAfter=10,
            )
            elements.append(
                Paragraph(f"Step {step.step_number}: {step.title}", step_header_style)
            )

            # Step description
            description_style = ParagraphStyle(
                "Description",
                parent=styles["Normal"],
                fontSize=11,
                spaceAfter=10,
                leading=14,
            )
            elements.append(Paragraph(step.description, description_style))

            # Detailed description (if available from LLM)
            if step.detail_description:
                elements.append(Paragraph(step.detail_description, description_style))

            elements.append(Spacer(1, 0.15 * inch))

            # Assembly sequence steps
            if step.assembly_sequence:
                sequence_style = ParagraphStyle(
                    "Sequence",
                    parent=styles["Normal"],
                    fontSize=10,
                    leftIndent=0.2 * inch,
                    spaceAfter=5,
                )
                elements.append(Paragraph("<b>Sequence:</b>", styles["Normal"]))
                for seq_item in step.assembly_sequence:
                    elements.append(Paragraph(f"• {seq_item}", sequence_style))
                elements.append(Spacer(1, 0.1 * inch))

            # Warnings
            if step.warnings:
                warning_style = ParagraphStyle(
                    "Warning",
                    parent=styles["Normal"],
                    fontSize=10,
                    textColor=colors.HexColor("#cc0000"),
                    leftIndent=0.2 * inch,
                    spaceAfter=5,
                )
                elements.append(Paragraph("<b>⚠ Warnings:</b>", styles["Normal"]))
                for warning in step.warnings:
                    elements.append(Paragraph(f"• {warning}", warning_style))
                elements.append(Spacer(1, 0.1 * inch))

            # Tips
            if step.tips:
                tips_style = ParagraphStyle(
                    "Tips",
                    parent=styles["Normal"],
                    fontSize=10,
                    textColor=colors.HexColor("#0066cc"),
                    leftIndent=0.2 * inch,
                    spaceAfter=5,
                )
                elements.append(Paragraph("<b>💡 Tips:</b>", styles["Normal"]))
                for tip in step.tips:
                    elements.append(Paragraph(f"• {tip}", tips_style))
                elements.append(Spacer(1, 0.1 * inch))

            # SVG Diagram (if available)
            if step.svg_diagram:
                try:
                    diagram_image = self._svg_to_image(step.svg_diagram)
                    if diagram_image:
                        elements.append(diagram_image)
                except Exception as e:
                    logger.warning(f"Failed to embed SVG diagram for step {step.step_number}: {e}")

            # Confidence score and generation info
            if step.confidence_score < 1.0:
                confidence_style = ParagraphStyle(
                    "Confidence",
                    parent=styles["Normal"],
                    fontSize=8,
                    textColor=colors.HexColor("#999999"),
                    spaceAfter=5,
                )
                confidence_text = "LLM-Generated" if step.is_llm_generated else "Rules-Based"
                elements.append(
                    Paragraph(
                        f"<i>{confidence_text} · Confidence: {step.confidence_score:.0%}</i>",
                        confidence_style,
                    )
                )

            # Page break between steps (except the last one)
            if i < len(assembly_steps):
                elements.append(PageBreak())

        return elements

    def _svg_to_image(self, svg_content: str) -> Optional[Image]:
        """
        Convert SVG string to PIL Image and return reportlab Image object.

        Note: This is a simplified version. For production, consider using
        svglib or similar libraries for better SVG support.

        Args:
            svg_content: SVG XML string

        Returns:
            reportlab Image object or None if conversion fails
        """
        try:
            # Note: Direct SVG embedding in reportlab is limited
            # For better support, install svglib: pip install svglib
            # from svglib.svglib import svg2rlg
            # drawing = svg2rlg(BytesIO(svg_content.encode()))
            # if drawing:
            #     return drawing

            # For now, we'll just log that SVG embedding is attempted
            # In production, use svglib for proper SVG rendering
            logger.debug("SVG diagram would be embedded here (requires svglib)")
            return None

        except Exception as e:
            logger.debug(f"SVG to image conversion failed: {e}")
            return None

    async def process(self, data: dict) -> dict:
        """
        Process stage (required by PipelineStage).

        Not used for PDF generation as it's called directly.
        """
        return data
