import React, { useState } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { locationAPI } from '../services/api';
import LocationSearchBar from '../components/LocationSearchBar';
import Badge from '../components/Badge';
import EmptyState from '../components/EmptyState';

export default function VetsScreen({ navigation }) {
  const [vets, setVets] = useState([]);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (params) => {
    try { const res = await locationAPI.vets(params); setVets(res.data.vets || []); setSearched(true); } catch {}
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Find Veterinarians</Text>
      </View>
      <LocationSearchBar onSearch={handleSearch} placeholder="Search vets near you..." />
      <FlatList data={vets} keyExtractor={(v) => String(v.id)} contentContainerStyle={styles.list}
        ListEmptyComponent={
          searched ? <EmptyState icon="heart" title="No vets found" /> :
          <EmptyState icon="search" title="Search for vets" message="Enter your location to find nearby veterinarians" />
        }
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.card} onPress={() => navigation.navigate('VendorProfile', { vendorId: item.id })}>
            <View style={styles.cardHeader}>
              <Text style={styles.name}>{item.name}</Text>
              {item.is_online ? <Badge text="Open" color={COLORS.success} /> : <Badge text="Closed" color={COLORS.grey} />}
            </View>
            {item.description && <Text style={styles.desc} numberOfLines={2}>{item.description}</Text>}
            <View style={styles.meta}>
              <Feather name="map-pin" size={13} color={COLORS.grey} />
              <Text style={styles.metaText}>{item.city} • {item.distance} km</Text>
            </View>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: { backgroundColor: COLORS.primary, paddingTop: 50, paddingBottom: 16, paddingHorizontal: SPACING.lg },
  title: { fontSize: 24, fontWeight: '700', color: COLORS.white },
  list: { padding: SPACING.md },
  card: { backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: SPACING.md, marginBottom: 10, ...SHADOWS.small },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  name: { fontSize: 16, fontWeight: '600', color: COLORS.dark, flex: 1 },
  desc: { fontSize: 13, color: COLORS.grey, marginTop: 6 },
  meta: { flexDirection: 'row', alignItems: 'center', marginTop: 8 },
  metaText: { fontSize: 12, color: COLORS.grey, marginLeft: 4 },
});
