import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, RefreshControl } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { handlersAPI } from '../services/api';
import Badge from '../components/Badge';
import EmptyState from '../components/EmptyState';
import GradientHeader from '../components/GradientHeader';

export default function MyHandlerBookingsScreen() {
  const [bookings, setBookings] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try { const res = await handlersAPI.bookings(); setBookings(res.data.bookings || []); } catch {}
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));
  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  const statusColor = (s) => s === 'delivered' ? COLORS.success : s === 'in_transit' ? COLORS.warning : COLORS.primary;

  return (
    <View style={styles.container}>
      <GradientHeader title="My Travel Bookings" subtitle="FurrWings handler bookings" />
      <FlatList data={bookings} keyExtractor={(_, i) => String(i)}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListEmptyComponent={<EmptyState icon="map" title="No travel bookings" message="Book a handler for pet travel" />}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.petName}>🐾 {item.pet_name}</Text>
              <Badge text={item.status} color={statusColor(item.status)} />
            </View>
            <Text style={styles.dest}>→ {item.destination}</Text>
            <Text style={styles.date}>Travel date: {item.travel_date}</Text>
            <Text style={styles.handler}>Handler: {item.handler_name}</Text>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  list: { padding: SPACING.md },
  card: { backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: SPACING.md, marginBottom: 10, ...SHADOWS.small },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  petName: { fontSize: 16, fontWeight: '600', color: COLORS.dark },
  dest: { fontSize: 14, color: COLORS.primary, marginTop: 6 },
  date: { fontSize: 13, color: COLORS.grey, marginTop: 4 },
  handler: { fontSize: 13, color: COLORS.grey, marginTop: 2 },
});
