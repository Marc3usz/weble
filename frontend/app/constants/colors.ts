// Custom color palette with dark/light theme support
export const PALETTE = {
  // Light theme
  light: {
    black: '#000000',
    dim_grey: '#66666e',
    rosy_granite: '#9999a1',
    alabaster_grey: '#e6e6e9',
    platinum: '#f4f4f6',
  },
  // Dark theme (inverted)
  dark: {
    black: '#ffffff',
    dim_grey: '#9999a1',
    rosy_granite: '#66666e',
    alabaster_grey: '#1a1a1d',
    platinum: '#0b0b0d',
  },
};

// Part type colors
export const PART_TYPE_COLORS = {
  light: {
    PANEL: '#66666e',        // dim_grey
    FASTENER: '#9999a1',     // rosy_granite
    HARDWARE: '#e6e6e9',     // alabaster_grey
    STRUCTURAL: '#000000',   // black
    OTHER: '#f4f4f6',        // platinum
  },
  dark: {
    PANEL: '#9999a1',        // inverted dim_grey
    FASTENER: '#66666e',     // inverted rosy_granite
    HARDWARE: '#1a1a1d',     // inverted alabaster_grey
    STRUCTURAL: '#ffffff',   // inverted black
    OTHER: '#0b0b0d',        // inverted platinum
  },
};

// UI colors
export const UI_COLORS = {
  light: {
    background: '#ffffff',
    surface: '#f4f4f6',
    border: '#e6e6e9',
    text: '#000000',
    textSecondary: '#66666e',
    accent: '#9999a1',
  },
  dark: {
    background: '#0b0b0d',
    surface: '#1a1a1d',
    border: '#3e3e43',
    text: '#ffffff',
    textSecondary: '#9999a1',
    accent: '#66666e',
  },
};

export function getTheme(isDark: boolean) {
  return isDark ? PALETTE.dark : PALETTE.light;
}

export function getPartColor(partType: string, isDark: boolean): string {
  const colors = isDark ? PART_TYPE_COLORS.dark : PART_TYPE_COLORS.light;
  return colors[partType as keyof typeof colors] || '#999999';
}

export function getUIColors(isDark: boolean) {
  return isDark ? UI_COLORS.dark : UI_COLORS.light;
}
