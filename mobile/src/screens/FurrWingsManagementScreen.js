import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { handlersAPI, petsAPI } from '../services/api';
import Card from '../components/Card';
import Badge from '../components/Badge';
import GradientHeader from '../components/GradientHeader';
import LoadingScreen from '../components/LoadingScreen';

const TRAVEL_DOCS = [
  { name: 'Health Certificate', icon: 'file-text' },
  { name: 'Vaccination Records', icon: 'shield' },
  { name: 'IATA Travel Crate Certificate', icon: 'box' },
  { name: 'Import Permit', icon: 'clipboard' },
  { name: 'Microchip Certificate', icon: 'cpu' },
  { name: 'Rabies Titer Test', icon: 'activity' },
];

export default function FurrWingsManagementScreen() {
  const [handlerBookings, setHandlerBookings] = useState([]);
  const [pets, setPets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [hRes, pRes] = await Promise.all([handlersAPI.bookings(), petsAPI.list()]);
        setHandlerBookings(hRes.data.bookings || []);
        setPets(pRes.data.pets || []);
      } catch {} finally { setLoading(false); }
    })();
  }, []);

  if (loading) return <LoadingScreen />;

  return (
    <ScrollView style={styles.container}>
      <GradientHeader title="FurrWings Management" subtitle="Travel data & document overview" />
      <View style={styles.content}>
        <Text style={styles.sectionTitle}>Passport Overview</Text>
        {pets.map((p, i) => (
          <Card key={i}>
            <Text style={styles.petName}>{p.species === 'Cat' ? '🐱' : '🐶'} {p.name}</Text>
            <Text style={styles.detail}>{p.breed || p.species}</Text>
          </Card>
        ))}
        {pets.length === 0 && <Text style={styles.emptyText}>No pets registered</Text>}

        <Text style={styles.sectionTitle}>All FurrWings Bookings</Text>
        {handlerBookings.map((b, i) => (
          <Card key={i}>
            <Text style={styles.petName}>{b.pet_name} → {b.destination}</Text>
            <Text style={styles.detail}>Travel: {b.travel_date} • Handler: {b.handler_name}</Text>
            <Badge text={b.status} color={b.status === 'delivered' ? COLORS.success : COLORS.primary} />
          </Card>
        ))}
        {handlerBookings.length === 0 && <Text style={styles.emptyText}>No bookings yet</Text>}

        <Text style={styles.sectionTitle}>International Travel Requirements</Text>
        <Text style={styles.infoText}>Documents needed for international pet travel vary by destination. Below is a general checklist:</Text>
        {TRAVEL_DOCS.map((doc, i) => (
          <Card key={i}>
            <View style={styles.docRow}>
              <Feather name={doc.icon} size={18} color={COLORS.primary} />
              <Text style={styles.docName}>{doc.name}</Text>
            </View>
          </Card>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: SPACING.md, paddingBottom: 40 },
  sectionTitle: { fontSize: 18, fontWeight: '700', color: COLORS.dark, marginTop: 20, marginBottom: 10 },
  petName: { fontSize: 15, fontWeight: '600', color: COLORS.dark },
  detail: { fontSize: 13, color: COLORS.grey, marginTop: 4, marginBottom: 6 },
  emptyText: { fontSize: 14, color: COLORS.grey, fontStyle: 'italic' },
  infoText: { fontSize: 14, color: COLORS.dark, marginBottom: 12, lineHeight: 20 },
  docRow: { flexDirection: 'row', alignItems: 'center' },
  docName: { fontSize: 15, color: COLORS.dark, marginLeft: 12 },
});
