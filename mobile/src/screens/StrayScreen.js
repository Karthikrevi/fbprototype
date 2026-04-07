import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, Image, RefreshControl } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { strayAPI } from '../services/api';
import Badge from '../components/Badge';
import EmptyState from '../components/EmptyState';
import GradientHeader from '../components/GradientHeader';
import LoadingScreen from '../components/LoadingScreen';

export default function StrayScreen({ navigation }) {
  const [strays, setStrays] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = async () => {
    try { const res = await strayAPI.list(); setStrays(res.data.strays || []); }
    catch {} finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);
  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  if (loading) return <LoadingScreen />;

  return (
    <View style={styles.container}>
      <GradientHeader title="Stray Tracker" subtitle="Help locate and rescue strays" />
      <FlatList data={strays} keyExtractor={(s) => s.uid || String(Math.random())}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListEmptyComponent={<EmptyState icon="map-pin" title="No stray reports" />}
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.card} onPress={() => navigation.navigate('StrayDetail', { strayUid: item.uid })}>
            {item.photo_url ? <Image source={{ uri: item.photo_url }} style={styles.image} /> : null}
            <View style={styles.cardBody}>
              <Text style={styles.name}>{item.description || 'Stray animal'}</Text>
              <View style={styles.meta}>
                <Feather name="map-pin" size={13} color={COLORS.grey} />
                <Text style={styles.metaText}>{item.location || 'Unknown location'}</Text>
              </View>
              <Badge text={item.status || 'reported'} color={item.status === 'rescued' ? COLORS.success : COLORS.warning} />
            </View>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  list: { padding: SPACING.md },
  card: { backgroundColor: COLORS.white, borderRadius: RADIUS.md, marginBottom: 12, overflow: 'hidden', ...SHADOWS.small },
  image: { width: '100%', height: 160 },
  cardBody: { padding: 14 },
  name: { fontSize: 15, fontWeight: '600', color: COLORS.dark },
  meta: { flexDirection: 'row', alignItems: 'center', marginTop: 6, marginBottom: 8 },
  metaText: { fontSize: 12, color: COLORS.grey, marginLeft: 4 },
});
