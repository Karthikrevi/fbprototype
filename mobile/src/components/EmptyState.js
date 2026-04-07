import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING } from '../constants/theme';

export default function EmptyState({ icon = 'inbox', title, message }) {
  return (
    <View style={styles.container}>
      <Feather name={icon} size={48} color={COLORS.lightGrey} />
      <Text style={styles.title}>{title || 'Nothing here yet'}</Text>
      {message && <Text style={styles.message}>{message}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: 'center', justifyContent: 'center', paddingVertical: 60 },
  title: { fontSize: 18, fontWeight: '600', color: COLORS.grey, marginTop: SPACING.md },
  message: { fontSize: 14, color: COLORS.textLight, marginTop: SPACING.xs, textAlign: 'center' },
});
