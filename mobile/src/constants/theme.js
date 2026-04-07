export const COLORS = {
  primary: '#667eea',
  secondary: '#764ba2',
  success: '#28a745',
  danger: '#dc3545',
  warning: '#ffc107',
  white: '#ffffff',
  light: '#f8f9fa',
  dark: '#333333',
  grey: '#6c757d',
  lightGrey: '#e9ecef',
  background: '#f5f3ff',
  cardBg: '#ffffff',
  border: '#dee2e6',
  text: '#333333',
  textLight: '#6c757d',
  gradientStart: '#667eea',
  gradientEnd: '#764ba2',
  star: '#ffc107',
  online: '#28a745',
  offline: '#dc3545',
};

export const FONTS = {
  regular: { fontSize: 14, color: COLORS.text },
  medium: { fontSize: 16, fontWeight: '500', color: COLORS.text },
  bold: { fontSize: 16, fontWeight: '700', color: COLORS.text },
  title: { fontSize: 24, fontWeight: '700', color: COLORS.dark },
  subtitle: { fontSize: 18, fontWeight: '600', color: COLORS.dark },
  small: { fontSize: 12, color: COLORS.textLight },
};

export const SHADOWS = {
  small: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  medium: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4,
  },
};

export const SPACING = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
};

export const RADIUS = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  full: 9999,
};
