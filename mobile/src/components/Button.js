import React from 'react';
import { TouchableOpacity, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { COLORS, RADIUS, SPACING } from '../constants/theme';

export default function Button({ title, onPress, variant = 'primary', loading, disabled, style }) {
  const bg = variant === 'secondary' ? COLORS.secondary
    : variant === 'success' ? COLORS.success
    : variant === 'danger' ? COLORS.danger
    : variant === 'outline' ? 'transparent'
    : COLORS.primary;

  const textColor = variant === 'outline' ? COLORS.primary : COLORS.white;
  const borderStyle = variant === 'outline' ? { borderWidth: 1.5, borderColor: COLORS.primary } : {};

  return (
    <TouchableOpacity
      style={[styles.btn, { backgroundColor: bg }, borderStyle, (disabled || loading) && styles.disabled, style]}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.8}
    >
      {loading ? (
        <ActivityIndicator color={textColor} />
      ) : (
        <Text style={[styles.text, { color: textColor }]}>{title}</Text>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  btn: {
    paddingVertical: 14,
    paddingHorizontal: SPACING.lg,
    borderRadius: RADIUS.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  text: { fontSize: 16, fontWeight: '600' },
  disabled: { opacity: 0.6 },
});
