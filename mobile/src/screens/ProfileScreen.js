import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { useAuth } from '../context/AuthContext';
import { petsAPI, bookingsAPI, ordersAPI } from '../services/api';
import Card from '../components/Card';
import Button from '../components/Button';

export default function ProfileScreen({ navigation }) {
  const { user, logout } = useAuth();
  const [pets, setPets] = useState([]);
  const [bookingCount, setBookingCount] = useState(0);
  const [orderCount, setOrderCount] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const [pRes, bRes, oRes] = await Promise.all([petsAPI.list(), bookingsAPI.list(), ordersAPI.list()]);
      setPets(pRes.data.pets || []);
      setBookingCount((bRes.data.bookings || []).length);
      setOrderCount((oRes.data.orders || []).length);
    } catch {}
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));
  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  const MenuItem = ({ icon, label, screen, params }) => (
    <TouchableOpacity style={styles.menuItem} onPress={() => navigation.navigate(screen, params)}>
      <Feather name={icon} size={20} color={COLORS.primary} />
      <Text style={styles.menuLabel}>{label}</Text>
      <Feather name="chevron-right" size={18} color={COLORS.grey} />
    </TouchableOpacity>
  );

  return (
    <ScrollView style={styles.container} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}>
      <View style={styles.header}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{(user?.name || user?.email || '?')[0].toUpperCase()}</Text>
        </View>
        <Text style={styles.name}>{user?.name || 'Pet Parent'}</Text>
        <Text style={styles.email}>{user?.email}</Text>
      </View>

      <View style={styles.statsRow}>
        <View style={styles.statBox}>
          <Text style={styles.statValue}>{pets.length}</Text>
          <Text style={styles.statLabel}>Pets</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={styles.statValue}>{bookingCount}</Text>
          <Text style={styles.statLabel}>Bookings</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={styles.statValue}>{orderCount}</Text>
          <Text style={styles.statLabel}>Orders</Text>
        </View>
      </View>

      <View style={styles.content}>
        <Text style={styles.sectionTitle}>My Pets</Text>
        {pets.slice(0, 3).map((p, i) => (
          <Card key={i} onPress={() => navigation.navigate('PetDetail', { petIndex: i })}>
            <View style={styles.petRow}>
              <Text style={styles.petEmoji}>{p.species === 'Cat' ? '🐱' : '🐶'}</Text>
              <View style={{ flex: 1 }}>
                <Text style={styles.petName}>{p.name}</Text>
                <Text style={styles.petBreed}>{p.breed || p.species}</Text>
              </View>
            </View>
          </Card>
        ))}
        <TouchableOpacity onPress={() => navigation.navigate('Pets')} style={styles.viewAll}>
          <Text style={styles.viewAllText}>View all pets →</Text>
        </TouchableOpacity>

        <Text style={styles.sectionTitle}>Menu</Text>
        <Card style={{ padding: 0 }}>
          <MenuItem icon="calendar" label="My Bookings" screen="Bookings" />
          <MenuItem icon="package" label="My Orders" screen="Orders" />
          <MenuItem icon="message-circle" label="Messages" screen="Conversations" />
          <MenuItem icon="globe" label="Travel Bookings" screen="MyHandlerBookings" />
          <MenuItem icon="settings" label="Settings & Privacy" screen="Settings" />
        </Card>

        <Button title="Sign Out" variant="outline" onPress={logout} style={{ marginTop: 24, marginBottom: 40 }} />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: { backgroundColor: COLORS.primary, paddingTop: 50, paddingBottom: 30, alignItems: 'center' },
  avatar: { width: 70, height: 70, borderRadius: 35, backgroundColor: 'rgba(255,255,255,0.2)', alignItems: 'center', justifyContent: 'center' },
  avatarText: { fontSize: 28, fontWeight: '700', color: COLORS.white },
  name: { fontSize: 20, fontWeight: '700', color: COLORS.white, marginTop: 10 },
  email: { fontSize: 14, color: 'rgba(255,255,255,0.8)', marginTop: 4 },
  statsRow: { flexDirection: 'row', marginTop: -20, paddingHorizontal: SPACING.md },
  statBox: { flex: 1, backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: 14, marginHorizontal: 4, alignItems: 'center', ...SHADOWS.small },
  statValue: { fontSize: 20, fontWeight: '700', color: COLORS.primary },
  statLabel: { fontSize: 12, color: COLORS.grey, marginTop: 2 },
  content: { padding: SPACING.md, marginTop: 8 },
  sectionTitle: { fontSize: 18, fontWeight: '700', color: COLORS.dark, marginTop: 16, marginBottom: 10 },
  petRow: { flexDirection: 'row', alignItems: 'center' },
  petEmoji: { fontSize: 32, marginRight: 12 },
  petName: { fontSize: 15, fontWeight: '600', color: COLORS.dark },
  petBreed: { fontSize: 12, color: COLORS.grey },
  viewAll: { paddingVertical: 8 },
  viewAllText: { fontSize: 14, color: COLORS.primary, fontWeight: '500' },
  menuItem: { flexDirection: 'row', alignItems: 'center', paddingVertical: 14, paddingHorizontal: SPACING.md, borderBottomWidth: 1, borderBottomColor: COLORS.lightGrey },
  menuLabel: { flex: 1, fontSize: 15, color: COLORS.dark, marginLeft: 12 },
});
