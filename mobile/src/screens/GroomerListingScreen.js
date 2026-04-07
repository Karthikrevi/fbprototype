import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { vendorAPI } from '../services/api';
import Badge from '../components/Badge';
import LoadingScreen from '../components/LoadingScreen';

export default function GroomerListingScreen({ route, navigation }) {
  const { vendorId } = route.params;
  const [groomers, setGroomers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { const res = await vendorAPI.groomers(vendorId); setGroomers(res.data.groomers || []); }
      catch {} finally { setLoading(false); }
    })();
  }, [vendorId]);

  if (loading) return <LoadingScreen />;

  return (
    <View style={styles.container}>
      <FlatList data={groomers} keyExtractor={(g) => String(g.id)}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.card} onPress={() => navigation.navigate('GroomerProfile', { employeeId: item.id })}>
            <Text style={styles.name}>{item.name}</Text>
            <Text style={styles.position}>{item.position}</Text>
            <View style={styles.statsRow}>
              <Text style={styles.stat}>⭐ {item.avg_rating}</Text>
              <Text style={styles.stat}>{item.total_reviews} reviews</Text>
              {item.is_certified ? <Badge text="Certified" color={COLORS.success} /> : null}
              {item.is_groomer_of_month ? <Badge text="⭐ GOTM" color={COLORS.warning} /> : null}
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
  name: { fontSize: 17, fontWeight: '600', color: COLORS.dark },
  position: { fontSize: 13, color: COLORS.grey, marginTop: 2 },
  statsRow: { flexDirection: 'row', alignItems: 'center', marginTop: 8, gap: 10 },
  stat: { fontSize: 13, color: COLORS.dark },
});
