import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { handlersAPI, bookingsAPI } from '../services/api';
import Card from '../components/Card';
import Badge from '../components/Badge';
import GradientHeader from '../components/GradientHeader';
import LoadingScreen from '../components/LoadingScreen';

export default function FurrWingsServicesScreen() {
  const [handlerBookings, setHandlerBookings] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [hRes, bRes] = await Promise.all([handlersAPI.bookings(), bookingsAPI.list()]);
        setHandlerBookings(hRes.data.bookings || []);
        setBookings(bRes.data.bookings || []);
      } catch {} finally { setLoading(false); }
    })();
  }, []);

  if (loading) return <LoadingScreen />;

  const vetBookings = bookings.filter(b => b.service?.toLowerCase().includes('vet'));
  const inTransit = handlerBookings.filter(b => b.status === 'in_transit');

  return (
    <ScrollView style={styles.container}>
      <GradientHeader title="FurrWings Services" subtitle="Track all FurrWings activities" />
      <View style={styles.content}>
        <Text style={styles.sectionTitle}>Transport Status</Text>
        {inTransit.length > 0 ? inTransit.map((b, i) => (
          <Card key={i}>
            <View style={styles.row}>
              <Feather name="navigation" size={18} color={COLORS.primary} />
              <View style={styles.rowInfo}>
                <Text style={styles.petName}>🐾 {b.pet_name}</Text>
                <Text style={styles.dest}>→ {b.destination}</Text>
                <Badge text="In Transit" color={COLORS.warning} />
              </View>
            </View>
          </Card>
        )) : <Text style={styles.emptyText}>No active transports</Text>}

        <Text style={styles.sectionTitle}>Vet Appointments via FurrWings</Text>
        {vetBookings.length > 0 ? vetBookings.map((b, i) => (
          <Card key={i}>
            <Text style={styles.petName}>{b.service}</Text>
            <Text style={styles.detail}>{b.date} at {b.time}</Text>
            <Badge text={b.status} color={b.status === 'completed' ? COLORS.success : COLORS.primary} />
          </Card>
        )) : <Text style={styles.emptyText}>No vet appointments tracked</Text>}

        <Text style={styles.sectionTitle}>All Travel Bookings</Text>
        {handlerBookings.length > 0 ? handlerBookings.map((b, i) => (
          <Card key={i}>
            <Text style={styles.petName}>{b.pet_name} → {b.destination}</Text>
            <Text style={styles.detail}>Travel: {b.travel_date} • Handler: {b.handler_name}</Text>
            <Badge text={b.status} color={b.status === 'delivered' ? COLORS.success : COLORS.primary} />
          </Card>
        )) : <Text style={styles.emptyText}>No travel bookings</Text>}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: SPACING.md, paddingBottom: 40 },
  sectionTitle: { fontSize: 18, fontWeight: '700', color: COLORS.dark, marginTop: 20, marginBottom: 10 },
  row: { flexDirection: 'row', alignItems: 'center' },
  rowInfo: { marginLeft: 12, flex: 1 },
  petName: { fontSize: 15, fontWeight: '600', color: COLORS.dark },
  dest: { fontSize: 13, color: COLORS.primary, marginTop: 2, marginBottom: 6 },
  detail: { fontSize: 13, color: COLORS.grey, marginTop: 4, marginBottom: 6 },
  emptyText: { fontSize: 14, color: COLORS.grey, fontStyle: 'italic' },
});
