import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, RefreshControl } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { petsAPI } from '../services/api';
import EmptyState from '../components/EmptyState';
import GradientHeader from '../components/GradientHeader';

export default function PetsScreen({ navigation }) {
  const [pets, setPets] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try { const res = await petsAPI.list(); setPets(res.data.pets || []); } catch {}
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  const renderPet = ({ item, index }) => (
    <TouchableOpacity style={styles.card} onPress={() => navigation.navigate('PetDetail', { petIndex: index })}>
      <Text style={styles.petEmoji}>{item.species === 'Cat' ? '🐱' : '🐶'}</Text>
      <View style={styles.petInfo}>
        <Text style={styles.petName}>{item.name}</Text>
        <Text style={styles.petDetail}>{item.breed || item.species} {item.birthday ? `• Born ${item.birthday}` : ''}</Text>
      </View>
      <Feather name="chevron-right" size={20} color={COLORS.grey} />
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <GradientHeader title="Your Pets" subtitle={`${pets.length} pet${pets.length !== 1 ? 's' : ''} registered`} />
      <FlatList data={pets} renderItem={renderPet} keyExtractor={(_, i) => String(i)}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListEmptyComponent={<EmptyState icon="heart" title="No pets yet" message="Add your first pet to get started" />}
        ListFooterComponent={
          <TouchableOpacity style={styles.addBtn} onPress={() => navigation.navigate('AddPet')}>
            <Feather name="plus" size={20} color={COLORS.primary} />
            <Text style={styles.addText}>Add New Pet</Text>
          </TouchableOpacity>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  list: { padding: SPACING.md },
  card: { backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: SPACING.md, flexDirection: 'row', alignItems: 'center', marginBottom: 10, ...SHADOWS.small },
  petEmoji: { fontSize: 36, marginRight: 14 },
  petInfo: { flex: 1 },
  petName: { fontSize: 16, fontWeight: '600', color: COLORS.dark },
  petDetail: { fontSize: 13, color: COLORS.grey, marginTop: 2 },
  addBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', padding: 16, backgroundColor: COLORS.white, borderRadius: RADIUS.md, borderWidth: 1.5, borderColor: COLORS.primary, borderStyle: 'dashed', marginTop: 8 },
  addText: { fontSize: 15, color: COLORS.primary, fontWeight: '600', marginLeft: 8 },
});
