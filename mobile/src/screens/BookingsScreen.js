import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, RefreshControl } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { bookingsAPI } from '../services/api';
import Badge from '../components/Badge';
import EmptyState from '../components/EmptyState';
import GradientHeader from '../components/GradientHeader';

export default function BookingsScreen({ navigation }) {
  const [bookings, setBookings] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try { const res = await bookingsAPI.list(); setBookings(res.data.bookings || []); } catch {}
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));
  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  const statusColor = (s) => s === 'completed' ? COLORS.success : s === 'cancelled' ? COLORS.danger : s === 'confirmed' ? COLORS.primary : COLORS.warning;

  return (
    <View style={styles.container}>
      <GradientHeader title="My Bookings" subtitle={`${bookings.length} booking${bookings.length !== 1 ? 's' : ''}`} />
      <FlatList data={bookings} keyExtractor={(_, i) => String(i)}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListEmptyComponent={<EmptyState icon="calendar" title="No bookings" message="Book a grooming session to get started" />}
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.card}
            onPress={() => item.status === 'completed' ? navigation.navigate('Review', { bookingId: item.id }) : null}>
            <View style={styles.cardHeader}>
              <Text style={styles.service}>{item.service}</Text>
              <Badge text={item.status} color={statusColor(item.status)} />
            </View>
            <Text style={styles.vendor}>{item.vendor_name}</Text>
            <Text style={styles.detail}>🐾 {item.pet_name} • 📅 {item.date} at {item.time}</Text>
            {item.status === 'completed' && !item.reviewed && (
              <TouchableOpacity style={styles.reviewBtn} onPress={() => navigation.navigate('Review', { bookingId: item.id })}>
                <Text style={styles.reviewText}>Leave a Review</Text>
              </TouchableOpacity>
            )}
          </TouchableOpacity>
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
  service: { fontSize: 16, fontWeight: '600', color: COLORS.dark },
  vendor: { fontSize: 14, color: COLORS.primary, marginTop: 4 },
  detail: { fontSize: 13, color: COLORS.grey, marginTop: 6 },
  reviewBtn: { marginTop: 10, paddingVertical: 8, paddingHorizontal: 16, backgroundColor: COLORS.primary + '10', borderRadius: RADIUS.sm, alignSelf: 'flex-start' },
  reviewText: { fontSize: 13, fontWeight: '600', color: COLORS.primary },
});
