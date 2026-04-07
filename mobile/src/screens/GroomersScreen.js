import React, { useState } from 'react';
import { View, Text, StyleSheet, FlatList, Image, TouchableOpacity } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { groomersAPI } from '../services/api';
import LocationSearchBar from '../components/LocationSearchBar';
import EmptyState from '../components/EmptyState';
import Badge from '../components/Badge';

export default function GroomersScreen({ navigation }) {
  const [vendors, setVendors] = useState([]);
  const [locationName, setLocationName] = useState('');
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (params) => {
    setLoading(true);
    try {
      const res = await groomersAPI.search(params);
      setVendors(res.data.vendors || []);
      setLocationName(res.data.location_name || '');
      setSearched(true);
    } catch {} finally { setLoading(false); }
  };

  const renderVendor = ({ item }) => (
    <TouchableOpacity style={styles.card} onPress={() => navigation.navigate('VendorProfile', { vendorId: item.id })} activeOpacity={0.7}>
      <Image source={{ uri: item.image }} style={styles.image} />
      <View style={styles.cardBody}>
        <View style={styles.cardHeader}>
          <Text style={styles.name} numberOfLines={1}>{item.name}</Text>
          {item.is_online ? <Badge text="Online" color={COLORS.success} /> : <Badge text="Offline" color={COLORS.grey} />}
        </View>
        <Text style={styles.desc} numberOfLines={2}>{item.description}</Text>
        <View style={styles.meta}>
          <Feather name="map-pin" size={13} color={COLORS.grey} />
          <Text style={styles.metaText}>{item.city} • {item.distance} km</Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Find Groomers</Text>
        {locationName ? <Text style={styles.locationLabel}>Near {locationName}</Text> : null}
      </View>
      <LocationSearchBar onSearch={handleSearch} placeholder="Search by city..." />
      <FlatList data={vendors} renderItem={renderVendor} keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          searched ? <EmptyState icon="scissors" title="No groomers found" message="Try a different location" /> :
          <EmptyState icon="search" title="Search for groomers" message="Enter your city or use GPS to find nearby groomers" />
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: { backgroundColor: COLORS.primary, paddingTop: 50, paddingBottom: 16, paddingHorizontal: SPACING.lg },
  title: { fontSize: 24, fontWeight: '700', color: COLORS.white },
  locationLabel: { fontSize: 13, color: 'rgba(255,255,255,0.8)', marginTop: 4 },
  list: { padding: SPACING.md },
  card: { backgroundColor: COLORS.white, borderRadius: RADIUS.md, marginBottom: 12, overflow: 'hidden', ...SHADOWS.small },
  image: { width: '100%', height: 140 },
  cardBody: { padding: 14 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  name: { fontSize: 17, fontWeight: '700', color: COLORS.dark, flex: 1, marginRight: 8 },
  desc: { fontSize: 13, color: COLORS.grey, marginTop: 6 },
  meta: { flexDirection: 'row', alignItems: 'center', marginTop: 8 },
  metaText: { fontSize: 12, color: COLORS.grey, marginLeft: 4 },
});
