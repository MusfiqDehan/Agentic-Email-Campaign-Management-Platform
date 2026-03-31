export const API_URL =
  process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8001/api/v1';

export const WS_URL =
  process.env.EXPO_PUBLIC_WS_URL ?? 'ws://localhost:8001';

export const COLORS = {
  primary: '#7c3aed',
  primaryLight: '#8b5cf6',
  primaryDark: '#5b21b6',
  background: '#0f172a',
  surface: '#1e293b',
  surfaceLight: '#334155',
  border: '#334155',
  text: '#f8fafc',
  textMuted: '#94a3b8',
  textSecondary: '#cbd5e1',
  success: '#22c55e',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#3b82f6',
  white: '#ffffff',
  black: '#000000',
};

export const FONTS = {
  regular: 'System',
  medium: 'System',
  bold: 'System',
};

export const SPACING = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const BORDER_RADIUS = {
  sm: 6,
  md: 10,
  lg: 16,
  xl: 24,
  full: 9999,
};
