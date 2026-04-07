import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, RefreshControl } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { ordersAPI } from '../services/api';
import Badge from '../components/Badge';
import EmptyState from '../components/EmptyState';
import GradientHeader from '../components/GradientHeader';

export default function OrdersScreen({ navigation }) {
  const [orders, setOrders] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try { const res = await ordersAPI.list(); setOrders(res.data.orders || []); } catch {}
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));
  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  return (
    <View style={styles.container}>
      <GradientHeader title="My Orders" subtitle={`${orders.length} order${orders.length !== 1 ? 's' : ''}`} />
      <FlatList data={orders} keyExtractor={(_, i) => String(i)}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListEmptyComponent={<EmptyState icon="package" title="No orders yet" message="Browse the marketplace to place your first order" />}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.orderId}>Order #{item.id}</Text>
              <Badge text={item.status || 'pending'} color={item.status === 'delivered' ? COLORS.success : COLORS.primary} />
            </View>
            <Text style={styles.vendor}>{item.vendor_name}</Text>
            <Text style={styles.date}>{item.created_at}</Text>
            {item.items?.map((p, j) => (
              <Text key={j} style={styles.itemText}>{p.quantity}x {p.name} - ${p.price}</Text>
            ))}
            <View style={styles.totalRow}>
              <Text style={styles.totalLabel}>Total</Text>
              <Text style={styles.totalAmount}>${item.total?.toFixed(2)}</Text>
            </View>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  list: { padding: SPACING.md },
  card: { backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: SPACING.md, marginBottom: 12, ...SHADOWS.small },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  orderId: { fontSize: 16, fontWeight: '700', color: COLORS.dark },
  vendor: { fontSize: 14, color: COLORS.primary, marginTop: 4 },
  date: { fontSize: 12, color: COLORS.grey, marginTop: 2 },
  itemText: { fontSize: 13, color: COLORS.dark, marginTop: 6 },
  totalRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 10, paddingTop: 8, borderTopWidth: 1, borderTopColor: COLORS.lightGrey },
  totalLabel: { fontSize: 14, fontWeight: '600', color: COLORS.dark },
  totalAmount: { fontSize: 16, fontWeight: '700', color: COLORS.primary },
});
