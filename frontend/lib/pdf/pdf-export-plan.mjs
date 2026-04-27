export function selectStepsForPdf(steps, stepIndex) {
  if (typeof stepIndex !== "number") {
    return steps;
  }

  return steps.filter((_, index) => index === stepIndex);
}

export function buildPdfFileName(modelId, stepNumber) {
  if (typeof stepNumber === "number") {
    return `weble-${modelId}-krok-${stepNumber}.pdf`;
  }

  return `weble-${modelId}-instrukcja.pdf`;
}

export function summarizePartsForPdf(parts) {
  return parts.map((part) => {
    const dims = part.dimensions || {};
    const width = Number.isFinite(dims.width) ? Math.round(dims.width) : 0;
    const height = Number.isFinite(dims.height) ? Math.round(dims.height) : 0;
    const depth = Number.isFinite(dims.depth) ? Math.round(dims.depth) : 0;

    return {
      id: part.id,
      label: part.name || part.id,
      quantity: part.quantity,
      typeLabel: part.part_type || "part",
      dimensionsLabel:
        width && height && depth ? `${width} x ${height} x ${depth} mm` : "-",
    };
  });
}
