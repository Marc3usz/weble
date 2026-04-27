import { jsPDF } from "jspdf";

import type { AssemblyStep, Part } from "@/types";
import {
  buildPdfFileName,
  selectStepsForPdf,
  summarizePartsForPdf,
} from "./pdf-export-plan.mjs";

type StepCapture = (stepIndex: number) => Promise<string | null>;

interface ExportAssemblyPdfOptions {
  modelId: string;
  steps: AssemblyStep[];
  parts: Part[];
  stepIndex?: number;
  captureStepScreenshot: StepCapture;
}

interface PdfPartSummary {
  id: string;
  label: string;
  quantity: number;
  typeLabel: string;
  dimensionsLabel: string;
}

const PAGE_WIDTH = 595.28;
const PAGE_HEIGHT = 841.89;
const PAGE_MARGIN = 40;
const HEADER_COLOR = [140, 120, 180] as const;
const ACCENT_COLOR = [232, 226, 245] as const;
const TEXT_COLOR = [45, 45, 55] as const;

export async function exportAssemblyPdf({
  modelId,
  steps,
  parts,
  stepIndex,
  captureStepScreenshot,
}: ExportAssemblyPdfOptions): Promise<void> {
  if (!steps.length) {
    throw new Error("Brak krokow instrukcji do eksportu.");
  }

  const selectedSteps = selectStepsForPdf(steps, stepIndex);
  const selectedIndices =
    typeof stepIndex === "number" ? [stepIndex] : steps.map((_, index) => index);
  const pdf = new jsPDF({ unit: "pt", format: "a4" });

  drawTitlePage(pdf, modelId, selectedSteps.length, parts.length);
  pdf.addPage();
  drawPartsPage(pdf, parts);

  for (let orderIndex = 0; orderIndex < selectedSteps.length; orderIndex += 1) {
    const originalStepIndex = selectedIndices[orderIndex];
    const step = selectedSteps[orderIndex];
    const screenshot = await captureStepScreenshot(originalStepIndex);
    const svgPreview = step.exploded_view_svg || step.svg_diagram;
    const svgImage = svgPreview ? await convertSvgToPngDataUrl(svgPreview) : null;

    pdf.addPage();
    drawStepPage(pdf, step, screenshot, svgImage);
  }

  const fileName = buildPdfFileName(
    modelId,
    typeof stepIndex === "number" ? steps[stepIndex]?.step_number : undefined
  );
  pdf.save(fileName);
}

function drawTitlePage(
  pdf: jsPDF,
  modelId: string,
  stepCount: number,
  partCount: number
): void {
  fillPage(pdf, 248, 246, 252);
  pdf.setFillColor(...HEADER_COLOR);
  pdf.roundedRect(PAGE_MARGIN, PAGE_MARGIN, PAGE_WIDTH - PAGE_MARGIN * 2, 180, 28, 28, "F");

  pdf.setTextColor(255, 255, 255);
  pdf.setFont("helvetica", "bold");
  pdf.setFontSize(26);
  pdf.text("WEBLE Assembly Guide", PAGE_MARGIN + 28, PAGE_MARGIN + 52);

  pdf.setFontSize(13);
  pdf.setFont("helvetica", "normal");
  pdf.text("Techniczna instrukcja montazu wygenerowana przez system WEBLE", PAGE_MARGIN + 28, PAGE_MARGIN + 84);

  pdf.setFontSize(16);
  pdf.setFont("helvetica", "bold");
  pdf.text(`Model: ${modelId}`, PAGE_MARGIN + 28, PAGE_MARGIN + 128);

  pdf.setFontSize(12);
  pdf.setFont("helvetica", "normal");
  pdf.text(`Liczba krokow: ${stepCount}`, PAGE_MARGIN + 28, PAGE_MARGIN + 154);
  pdf.text(`Liczba czesci: ${partCount}`, PAGE_MARGIN + 170, PAGE_MARGIN + 154);
  pdf.text(`Data eksportu: ${new Date().toLocaleDateString("pl-PL")}`, PAGE_MARGIN + 310, PAGE_MARGIN + 154);

  pdf.setTextColor(...TEXT_COLOR);
  pdf.setFont("helvetica", "bold");
  pdf.setFontSize(18);
  pdf.text("Co zawiera ten dokument", PAGE_MARGIN, 280);

  const lines = [
    "Sekwencje montazu w ustalonej kolejnosci.",
    "Opis techniczny, ostrzezenia i wskazowki dla kazdego kroku.",
    "Podglad 3D aktualnego etapu oraz diagram eksplodowany, jesli byl dostepny.",
  ];

  pdf.setFont("helvetica", "normal");
  pdf.setFontSize(12);
  lines.forEach((line, index) => {
    pdf.text(`• ${line}`, PAGE_MARGIN + 4, 320 + index * 24);
  });
}

function drawPartsPage(pdf: jsPDF, parts: Part[]): void {
  fillPage(pdf, 255, 255, 255);
  pdf.setTextColor(...TEXT_COLOR);
  pdf.setFont("helvetica", "bold");
  pdf.setFontSize(20);
  pdf.text("Zestaw czesci", PAGE_MARGIN, PAGE_MARGIN + 10);

  const summary = summarizePartsForPdf(parts) as PdfPartSummary[];
  const columns = [PAGE_MARGIN, PAGE_MARGIN + 180, PAGE_MARGIN + 320, PAGE_MARGIN + 420];
  let cursorY = PAGE_MARGIN + 46;

  pdf.setFillColor(...ACCENT_COLOR);
  pdf.roundedRect(PAGE_MARGIN, cursorY - 18, PAGE_WIDTH - PAGE_MARGIN * 2, 28, 12, 12, "F");
  pdf.setFontSize(11);
  pdf.setFont("helvetica", "bold");
  pdf.text("Czesc", columns[0], cursorY);
  pdf.text("Typ", columns[1], cursorY);
  pdf.text("Wymiary", columns[2], cursorY);
  pdf.text("Ilosc", columns[3], cursorY);

  cursorY += 28;
  pdf.setFont("helvetica", "normal");

  summary.forEach((part) => {
    if (cursorY > PAGE_HEIGHT - PAGE_MARGIN) {
      pdf.addPage();
      fillPage(pdf, 255, 255, 255);
      cursorY = PAGE_MARGIN + 20;
    }

    pdf.setDrawColor(230, 228, 235);
    pdf.line(PAGE_MARGIN, cursorY + 10, PAGE_WIDTH - PAGE_MARGIN, cursorY + 10);
    pdf.text(part.label, columns[0], cursorY);
    pdf.text(part.typeLabel, columns[1], cursorY);
    pdf.text(part.dimensionsLabel, columns[2], cursorY);
    pdf.text(String(part.quantity), columns[3], cursorY);
    cursorY += 26;
  });
}

function drawStepPage(
  pdf: jsPDF,
  step: AssemblyStep,
  screenshotDataUrl: string | null,
  svgDataUrl: string | null
): void {
  fillPage(pdf, 252, 251, 255);
  pdf.setFillColor(...HEADER_COLOR);
  pdf.roundedRect(PAGE_MARGIN, PAGE_MARGIN, PAGE_WIDTH - PAGE_MARGIN * 2, 64, 24, 24, "F");
  pdf.setTextColor(255, 255, 255);
  pdf.setFont("helvetica", "bold");
  pdf.setFontSize(16);
  pdf.text(`Krok ${step.step_number}`, PAGE_MARGIN + 24, PAGE_MARGIN + 30);
  pdf.setFontSize(20);
  pdf.text(step.title, PAGE_MARGIN + 24, PAGE_MARGIN + 54);

  pdf.setTextColor(...TEXT_COLOR);
  const leftX = PAGE_MARGIN;
  const rightX = PAGE_MARGIN + 280;
  const topY = PAGE_MARGIN + 94;
  const panelWidth = 235;
  const panelHeight = 180;

  drawImagePanel(pdf, leftX, topY, panelWidth, panelHeight, screenshotDataUrl, "Widok 3D kroku");
  drawImagePanel(pdf, rightX, topY, panelWidth, panelHeight, svgDataUrl, "Diagram kroku");

  let textY = topY + panelHeight + 28;
  textY = drawTextBlock(pdf, "Opis", step.description, textY);
  textY = drawTextBlock(pdf, "Szczegoly", step.detail_description || "-", textY);

  if (step.assembly_sequence?.length) {
    textY = drawListBlock(pdf, "Sekwencja", step.assembly_sequence, textY);
  }

  if (step.warnings?.length) {
    textY = drawListBlock(pdf, "Uwagi", step.warnings, textY, [180, 80, 80]);
  }

  if (step.tips?.length) {
    drawListBlock(pdf, "Wskazowki", step.tips, textY, [90, 120, 90]);
  }
}

function drawImagePanel(
  pdf: jsPDF,
  x: number,
  y: number,
  width: number,
  height: number,
  imageDataUrl: string | null,
  label: string
): void {
  pdf.setFillColor(255, 255, 255);
  pdf.roundedRect(x, y, width, height, 18, 18, "F");
  pdf.setDrawColor(224, 220, 232);
  pdf.roundedRect(x, y, width, height, 18, 18, "S");

  pdf.setFont("helvetica", "bold");
  pdf.setFontSize(11);
  pdf.setTextColor(...TEXT_COLOR);
  pdf.text(label, x + 14, y + 20);

  if (imageDataUrl) {
    pdf.addImage(imageDataUrl, "PNG", x + 14, y + 30, width - 28, height - 44, undefined, "FAST");
    return;
  }

  pdf.setFillColor(...ACCENT_COLOR);
  pdf.roundedRect(x + 14, y + 34, width - 28, height - 48, 12, 12, "F");
  pdf.setFont("helvetica", "normal");
  pdf.setFontSize(12);
  pdf.text("Brak podgladu dla tego elementu", x + 28, y + height / 2);
}

function drawTextBlock(pdf: jsPDF, heading: string, text: string, startY: number): number {
  pdf.setFont("helvetica", "bold");
  pdf.setFontSize(13);
  pdf.text(heading, PAGE_MARGIN, startY);

  pdf.setFont("helvetica", "normal");
  pdf.setFontSize(11);
  const lines = pdf.splitTextToSize(text || "-", PAGE_WIDTH - PAGE_MARGIN * 2);
  pdf.text(lines, PAGE_MARGIN, startY + 18);
  return startY + 18 + lines.length * 14 + 12;
}

function drawListBlock(
  pdf: jsPDF,
  heading: string,
  items: string[],
  startY: number,
  bulletColor: readonly [number, number, number] = HEADER_COLOR
): number {
  pdf.setFont("helvetica", "bold");
  pdf.setFontSize(13);
  pdf.text(heading, PAGE_MARGIN, startY);

  let cursorY = startY + 20;
  pdf.setFont("helvetica", "normal");
  pdf.setFontSize(11);

  items.forEach((item) => {
    pdf.setFillColor(...bulletColor);
    pdf.circle(PAGE_MARGIN + 5, cursorY - 4, 3, "F");
    const lines = pdf.splitTextToSize(item, PAGE_WIDTH - PAGE_MARGIN * 2 - 18);
    pdf.text(lines, PAGE_MARGIN + 16, cursorY);
    cursorY += lines.length * 14 + 8;
  });

  return cursorY + 4;
}

function fillPage(pdf: jsPDF, r: number, g: number, b: number): void {
  pdf.setFillColor(r, g, b);
  pdf.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, "F");
}

async function convertSvgToPngDataUrl(svgMarkup: string): Promise<string | null> {
  if (typeof window === "undefined") {
    return null;
  }

  const svgBlob = new Blob([svgMarkup], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(svgBlob);

  try {
    const image = await loadImage(url);
    const canvas = document.createElement("canvas");
    canvas.width = 1200;
    canvas.height = 800;
    const context = canvas.getContext("2d");

    if (!context) {
      return null;
    }

    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.drawImage(image, 0, 0, canvas.width, canvas.height);

    return canvas.toDataURL("image/png");
  } finally {
    URL.revokeObjectURL(url);
  }
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("Nie udalo sie wczytac obrazu do PDF."));
    image.src = src;
  });
}
