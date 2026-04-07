import React, { useState } from 'react';
import { View, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, RADIUS, SPACING } from '../constants/theme';
import { useLocation } from '../context/LocationContext';

export default function LocationSearchBar({ onSearch, placeholder }) {
  const [query, setQuery] = useState('');
  const { requestLocation, loading } = useLocation();

  const handleSearch = () => {
    if (query.trim()) onSearch({ location: query.trim() });
  };

  const handleGPS = async () => {
    const result = await requestLocation();
    if (result.success) onSearch({ lat: result.lat, lon: result.lon });
  };

  return (
    <View style={styles.container}>
      <View style={styles.inputRow}>
        <Feather name="search" size={18} color={COLORS.grey} />
        <TextInput
          style={styles.input}
          placeholder={placeholder || 'Search by city or area...'}
          placeholderTextColor={COLORS.grey}
          value={query}
          onChangeText={setQuery}
          onSubmitEditing={handleSearch}
          returnKeyType="search"
        />
        <TouchableOpacity onPress={handleGPS} disabled={loading} style={styles.gpsBtn}>
          {loading ? <ActivityIndicator size="small" color={COLORS.primary} /> :
            <Feather name="crosshair" size={20} color={COLORS.primary} />}
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { paddingHorizontal: SPACING.md, paddingVertical: SPACING.sm },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.md,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  input: { flex: 1, marginLeft: 8, fontSize: 15, color: COLORS.dark, paddingVertical: 6 },
  gpsBtn: { padding: 6 },
});
