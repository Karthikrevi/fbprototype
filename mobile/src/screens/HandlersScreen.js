import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { handlersAPI } from '../services/api';
import Badge from '../components/Badge';
import EmptyState from '../components/EmptyState';
import GradientHeader from '../components/GradientHeader';
import LoadingScreen from '../components/LoadingScreen';

export default function HandlersScreen({ navigation }) {
  const [handlers, setHandlers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { const res = await handlersAPI.list(); setHandlers(res.data.handlers || []); }
      catch {} finally { setLoading(false); }
    })();
  }, []);

  if (loading) return <LoadingScreen />;

  return (
    <View style={styles.container}>
      <GradientHeader title="FurrWings Handlers" subtitle="Certified pet travel handlers" />
      <FlatList data={handlers} keyExtractor={(h) => String(h.id)} contentContainerStyle={styles.list}
        ListEmptyComponent={<EmptyState icon="globe" title="No handlers available" />}
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.card} onPress={() => navigation.navigate('HandlerDetail', { handlerId: item.id })}>
            <View style={styles.cardHeader}>
              <Text style={styles.name}>{item.name}</Text>
              {item.is_available ? <Badge text="Available" color={COLORS.success} /> : <Badge text="Busy" color={COLORS.grey} />}
            </View>
            <Text style={styles.specialization}>{item.specialization}</Text>
            <View style={styles.meta}>
              <Feather name="map-pin" size={13} color={COLORS.grey} />
              <Text style={styles.metaText}>{item.city} • {item.experience_years}y exp</Text>
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
  card: { backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: SPACING.md, marginBottom: 10, ...SHADOWS.small },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  name: { fontSize: 16, fontWeight: '600', color: COLORS.dark },
  specialization: { fontSize: 13, color: COLORS.grey, marginTop: 4 },
  meta: { flexDirection: 'row', alignItems: 'center', marginTop: 8 },
  metaText: { fontSize: 12, color: COLORS.grey, marginLeft: 4 },
});
