// Utility functions
export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

export function formatDimensions(
  dimensions: { width: number; height: number; depth: number }
): string {
  return `${dimensions.width.toFixed(1)}×${dimensions.height.toFixed(1)}×${dimensions.depth.toFixed(1)} mm`;
}

export function formatVolume(volume: number): string {
  return `${volume.toFixed(2)} cm³`;
}

export function formatDuration(minutes: number): string {
  if (minutes < 1) return '< 1 minuta';
  if (minutes === 1) return '1 minuta';
  if (minutes < 5) return `${minutes} minuty`;
  return `${minutes} minut`;
}

export function formatConfidence(score: number): string {
  const percent = Math.round(score * 100);
  if (percent >= 80) return `✓ ${percent}%`;
  if (percent >= 60) return `⚠️ ${percent}%`;
  return `❌ ${percent}%`;
}

export function validateStepFile(file: File): boolean {
  const validExtensions = ['.step', '.stp'];
  const extension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
  return validExtensions.includes(extension);
}

export function classNames(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Template string replacement
export function interpolate(template: string, variables: Record<string, string | number>): string {
  return template.replace(/{{(\w+)}}/g, (_, key) => String(variables[key] || ''));
}
