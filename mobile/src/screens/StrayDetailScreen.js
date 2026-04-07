import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, Image } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS } from '../constants/theme';
import { strayAPI } from '../services/api';
import Card from '../components/Card';
import Badge from '../components/Badge';
import LoadingScreen from '../components/LoadingScreen';

export default function StrayDetailScreen({ route }) {
  const { strayUid } = route.params;
  const [stray, setStray] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { const res = await strayAPI.detail(strayUid); setStray(res.data.stray); }
      catch {} finally { setLoading(false); }
    })();
  }, [strayUid]);

  if (loading) return <LoadingScreen />;
  if (!stray) return <View style={styles.container}><Text style={{ textAlign: 'center', marginTop: 40 }}>Stray not found</Text></View>;

  return (
    <ScrollView style={styles.container}>
      {stray.photo_url ? <Image source={{ uri: stray.photo_url }} style={styles.image} /> : null}
      <View style={styles.content}>
        <Text style={styles.title}>{stray.description || 'Stray Animal'}</Text>
        <Badge text={stray.status || 'reported'} color={stray.status === 'rescued' ? COLORS.success : COLORS.warning} />

        <Card style={styles.infoCard}>
          <View style={styles.infoRow}>
            <Feather name="map-pin" size={16} color={COLORS.grey} />
            <Text style={styles.infoText}>{stray.location || 'Unknown location'}</Text>
          </View>
          {stray.reported_by && (
            <View style={styles.infoRow}>
              <Feather name="user" size={16} color={COLORS.grey} />
              <Text style={styles.infoText}>Reported by: {stray.reported_by}</Text>
            </View>
          )}
          {stray.reported_at && (
            <View style={styles.infoRow}>
              <Feather name="clock" size={16} color={COLORS.grey} />
              <Text style={styles.infoText}>{stray.reported_at}</Text>
            </View>
          )}
          {stray.ngo_name && (
            <View style={styles.infoRow}>
              <Feather name="heart" size={16} color={COLORS.grey} />
              <Text style={styles.infoText}>NGO: {stray.ngo_name}</Text>
            </View>
          )}
        </Card>

        {stray.updates && stray.updates.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Updates</Text>
            {stray.updates.map((u, i) => (
              <Card key={i}>
                <Text style={styles.updateText}>{u.text}</Text>
                <Text style={styles.updateDate}>{u.date}</Text>
              </Card>
            ))}
          </View>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  image: { width: '100%', height: 250 },
  content: { padding: SPACING.md },
  title: { fontSize: 22, fontWeight: '700', color: COLORS.dark, marginBottom: 8 },
  infoCard: { marginTop: 16 },
  infoRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8 },
  infoText: { fontSize: 14, color: COLORS.dark, marginLeft: 10 },
  section: { marginTop: 20 },
  sectionTitle: { fontSize: 18, fontWeight: '600', color: COLORS.dark, marginBottom: 10 },
  updateText: { fontSize: 14, color: COLORS.dark },
  updateDate: { fontSize: 12, color: COLORS.grey, marginTop: 4 },
});
