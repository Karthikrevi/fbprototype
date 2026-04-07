import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, FlatList, RefreshControl } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { useAuth } from '../context/AuthContext';
import { petsAPI } from '../services/api';
import Card from '../components/Card';

const TILES = [
  { key: 'marketplace', label: 'Marketplace', icon: 'shopping-bag', color: '#667eea', screen: 'Marketplace' },
  { key: 'groomers', label: 'Grooming', icon: 'scissors', color: '#764ba2', screen: 'Groomers' },
  { key: 'vets', label: 'Veterinary', icon: 'heart', color: '#e74c3c', screen: 'Vets' },
  { key: 'boarding', label: 'Boarding', icon: 'home', color: '#27ae60', screen: 'Boarding' },
  { key: 'bookings', label: 'My Bookings', icon: 'calendar', color: '#f39c12', screen: 'Bookings' },
  { key: 'orders', label: 'My Orders', icon: 'package', color: '#3498db', screen: 'Orders' },
  { key: 'messages', label: 'Messages', icon: 'message-circle', color: '#9b59b6', screen: 'Conversations' },
  { key: 'handlers', label: 'FurrWings Handlers', icon: 'globe', color: '#1abc9c', screen: 'Handlers' },
  { key: 'handler-bookings', label: 'My Travel Bookings', icon: 'map', color: '#e67e22', screen: 'MyHandlerBookings' },
  { key: 'furrwings', label: 'FurrWings Services', icon: 'send', color: '#2980b9', screen: 'FurrWingsServices' },
  { key: 'stray', label: 'Stray Tracker', icon: 'map-pin', color: '#c0392b', screen: 'StrayTracker' },
  { key: 'community', label: 'Community Posts', icon: 'users', color: '#8e44ad', screen: 'Community' },
  { key: 'report', label: 'Report Issues', icon: 'alert-triangle', color: '#d35400', screen: 'ReportIssues' },
  { key: 'furrwings-mgmt', label: 'FurrWings Management', icon: 'briefcase', color: '#16a085', screen: 'FurrWingsManagement' },
];

export default function HomeScreen({ navigation }) {
  const { user } = useAuth();
  const [pets, setPets] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const loadPets = useCallback(async () => {
    try { const res = await petsAPI.list(); setPets(res.data.pets || []); } catch {}
  }, []);

  useEffect(() => { loadPets(); }, [loadPets]);

  const onRefresh = async () => { setRefreshing(true); await loadPets(); setRefreshing(false); };

  const renderPet = ({ item, index }) => (
    <TouchableOpacity style={styles.petCard} onPress={() => navigation.navigate('PetDetail', { petIndex: index })}>
      <Text style={styles.petEmoji}>{item.species === 'Cat' ? '🐱' : '🐶'}</Text>
      <Text style={styles.petName} numberOfLines={1}>{item.name}</Text>
      <Text style={styles.petBreed} numberOfLines={1}>{item.breed || item.species}</Text>
    </TouchableOpacity>
  );

  return (
    <ScrollView style={styles.container} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}>
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Hello, {user?.name || user?.email?.split('@')[0]} 👋</Text>
          <Text style={styles.subGreeting}>What would you like to do today?</Text>
        </View>
        <TouchableOpacity onPress={() => navigation.navigate('Notifications')} style={styles.bellBtn}>
          <Feather name="bell" size={22} color={COLORS.white} />
        </TouchableOpacity>
      </View>

      <View style={styles.petsSection}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Your Pets</Text>
          <TouchableOpacity onPress={() => navigation.navigate('AddPet')}>
            <Feather name="plus-circle" size={22} color={COLORS.primary} />
          </TouchableOpacity>
        </View>
        {pets.length > 0 ? (
          <FlatList data={pets} renderItem={renderPet} keyExtractor={(_, i) => String(i)}
            horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 4 }} />
        ) : (
          <TouchableOpacity style={styles.addPetCard} onPress={() => navigation.navigate('AddPet')}>
            <Feather name="plus" size={24} color={COLORS.primary} />
            <Text style={styles.addPetText}>Add your first pet</Text>
          </TouchableOpacity>
        )}
      </View>

      <View style={styles.tilesGrid}>
        {TILES.map((tile) => (
          <TouchableOpacity key={tile.key} style={styles.tile}
            onPress={() => navigation.navigate(tile.screen)} activeOpacity={0.7}>
            <View style={[styles.tileIcon, { backgroundColor: tile.color + '15' }]}>
              <Feather name={tile.icon} size={22} color={tile.color} />
            </View>
            <Text style={styles.tileLabel} numberOfLines={2}>{tile.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <View style={{ height: 30 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: { backgroundColor: COLORS.primary, paddingTop: 50, paddingBottom: 24, paddingHorizontal: SPACING.lg, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  greeting: { fontSize: 22, fontWeight: '700', color: COLORS.white },
  subGreeting: { fontSize: 14, color: 'rgba(255,255,255,0.8)', marginTop: 4 },
  bellBtn: { padding: 8 },
  petsSection: { padding: SPACING.md },
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  sectionTitle: { fontSize: 18, fontWeight: '700', color: COLORS.dark },
  petCard: { backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: 14, marginRight: 12, width: 110, alignItems: 'center', ...SHADOWS.small },
  petEmoji: { fontSize: 32 },
  petName: { fontSize: 14, fontWeight: '600', color: COLORS.dark, marginTop: 6 },
  petBreed: { fontSize: 11, color: COLORS.grey, marginTop: 2 },
  addPetCard: { backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: 20, alignItems: 'center', borderStyle: 'dashed', borderWidth: 1.5, borderColor: COLORS.primary },
  addPetText: { fontSize: 14, color: COLORS.primary, marginTop: 8, fontWeight: '500' },
  tilesGrid: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: SPACING.sm },
  tile: { width: '25%', alignItems: 'center', paddingVertical: 14, paddingHorizontal: 4 },
  tileIcon: { width: 50, height: 50, borderRadius: 14, justifyContent: 'center', alignItems: 'center' },
  tileLabel: { fontSize: 11, color: COLORS.dark, marginTop: 6, textAlign: 'center', fontWeight: '500' },
});
