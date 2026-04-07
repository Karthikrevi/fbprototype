import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { handlersAPI } from '../services/api';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Button from '../components/Button';
import LoadingScreen from '../components/LoadingScreen';

export default function HandlerDetailScreen({ route, navigation }) {
  const { handlerId } = route.params;
  const [handler, setHandler] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { const res = await handlersAPI.detail(handlerId); setHandler(res.data.handler); }
      catch {} finally { setLoading(false); }
    })();
  }, [handlerId]);

  if (loading) return <LoadingScreen />;
  if (!handler) return <View style={styles.container}><Text>Handler not found</Text></View>;

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.name}>{handler.name}</Text>
        <Text style={styles.spec}>{handler.specialization}</Text>
        {handler.is_available ? <Badge text="Available" color={COLORS.success} /> : <Badge text="Currently Busy" color={COLORS.grey} />}
      </View>
      <View style={styles.content}>
        <Card>
          <Text style={styles.infoLabel}>Experience</Text>
          <Text style={styles.infoValue}>{handler.experience_years} years</Text>
          <Text style={styles.infoLabel}>Location</Text>
          <Text style={styles.infoValue}>{handler.city}</Text>
          <Text style={styles.infoLabel}>Certifications</Text>
          <Text style={styles.infoValue}>{handler.certifications || 'IATA Certified'}</Text>
        </Card>
        {handler.bio && <Card><Text style={styles.bio}>{handler.bio}</Text></Card>}
        <Button title="Book This Handler" onPress={() => navigation.navigate('HandlerBook', { handlerId, handler })}
          style={{ marginTop: 16 }} disabled={!handler.is_available} />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: { backgroundColor: COLORS.primary, paddingTop: 50, paddingBottom: 24, paddingHorizontal: SPACING.lg },
  name: { fontSize: 24, fontWeight: '700', color: COLORS.white },
  spec: { fontSize: 15, color: 'rgba(255,255,255,0.8)', marginTop: 4, marginBottom: 10 },
  content: { padding: SPACING.md },
  infoLabel: { fontSize: 12, color: COLORS.grey, marginTop: 10 },
  infoValue: { fontSize: 15, fontWeight: '500', color: COLORS.dark, marginTop: 2 },
  bio: { fontSize: 14, color: COLORS.dark, lineHeight: 20 },
});
