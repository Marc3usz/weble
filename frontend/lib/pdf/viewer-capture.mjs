export function extractViewerCanvasDataUrl(node) {
  const canvas = node?.querySelector?.("canvas");
  if (!canvas || typeof canvas.toDataURL !== "function") {
    return null;
  }

  try {
    return canvas.toDataURL("image/png");
  } catch {
    return null;
  }
}
