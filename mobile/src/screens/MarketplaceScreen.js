import React, { useState } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, Image } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { marketplaceAPI } from '../services/api';
import LocationSearchBar from '../components/LocationSearchBar';
import Badge from '../components/Badge';
import EmptyState from '../components/EmptyState';

export default function MarketplaceScreen({ navigation }) {
  const [vendors, setVendors] = useState([]);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (params) => {
    try {
      const res = await marketplaceAPI.search(params);
      setVendors(res.data.vendors || []);
      setSearched(true);
    } catch {}
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Marketplace</Text>
        <Text style={styles.subtitle}>Shop pet products from trusted vendors</Text>
      </View>
      <LocationSearchBar onSearch={handleSearch} placeholder="Search vendors near you..." />
      <FlatList data={vendors} keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list} numColumns={2} columnWrapperStyle={styles.row}
        ListEmptyComponent={
          searched ? <EmptyState icon="shopping-bag" title="No vendors found" /> :
          <EmptyState icon="search" title="Search for shops" message="Enter your location to find nearby pet product vendors" />
        }
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.card} onPress={() => navigation.navigate('VendorShop', { vendorId: item.id })}>
            <Image source={{ uri: item.image }} style={styles.image} />
            <View style={styles.cardBody}>
              <Text style={styles.name} numberOfLines={1}>{item.name}</Text>
              <Text style={styles.city}>{item.city} • {item.distance} km</Text>
              <Text style={styles.products}>{item.product_count} products</Text>
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
  subtitle: { fontSize: 13, color: 'rgba(255,255,255,0.8)', marginTop: 4 },
  list: { padding: SPACING.sm },
  row: { justifyContent: 'space-between' },
  card: { width: '48%', backgroundColor: COLORS.white, borderRadius: RADIUS.md, marginBottom: 12, overflow: 'hidden', ...SHADOWS.small },
  image: { width: '100%', height: 100 },
  cardBody: { padding: 10 },
  name: { fontSize: 14, fontWeight: '600', color: COLORS.dark },
  city: { fontSize: 11, color: COLORS.grey, marginTop: 2 },
  products: { fontSize: 11, color: COLORS.primary, marginTop: 4 },
});
