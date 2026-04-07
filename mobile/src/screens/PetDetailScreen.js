import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { petsAPI } from '../services/api';
import Card from '../components/Card';
import Badge from '../components/Badge';
import LoadingScreen from '../components/LoadingScreen';

export default function PetDetailScreen({ route, navigation }) {
  const { petIndex } = route.params;
  const [pet, setPet] = useState(null);
  const [bookings, setBookings] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await petsAPI.get(petIndex);
        setPet(res.data.pet);
        setBookings(res.data.bookings || []);
        setHistory(res.data.booking_history || []);
      } catch {} finally { setLoading(false); }
    })();
  }, [petIndex]);

  if (loading) return <LoadingScreen />;
  if (!pet) return <View style={styles.container}><Text style={styles.errorText}>Pet not found</Text></View>;

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.emoji}>{pet.species === 'Cat' ? '🐱' : '🐶'}</Text>
        <Text style={styles.name}>{pet.name}</Text>
        <Text style={styles.breed}>{pet.breed || pet.species}</Text>
        {pet.birthday ? <Text style={styles.detail}>Born: {pet.birthday}</Text> : null}
      </View>

      <View style={styles.actions}>
        <TouchableOpacity style={styles.actionBtn} onPress={() => navigation.navigate('EditPet', { pet, petIndex })}>
          <Feather name="edit-2" size={18} color={COLORS.primary} />
          <Text style={styles.actionText}>Edit</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionBtn} onPress={() => navigation.navigate('Passport', { petIndex })}>
          <Feather name="file-text" size={18} color={COLORS.primary} />
          <Text style={styles.actionText}>Passport</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Pet Info</Text>
        <Card>
          {pet.parent_name ? <Text style={styles.infoRow}>Parent: {pet.parent_name}</Text> : null}
          {pet.parent_phone ? <Text style={styles.infoRow}>Phone: {pet.parent_phone}</Text> : null}
          {pet.blood ? <Text style={styles.infoRow}>Blood Type: {pet.blood}</Text> : null}
        </Card>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Active Bookings ({bookings.length})</Text>
        {bookings.length > 0 ? bookings.slice(0, 5).map((b, i) => (
          <Card key={i}>
            <Text style={styles.bookService}>{b.service}</Text>
            <Text style={styles.bookDetail}>{b.date} at {b.time}</Text>
            <Badge text={b.status} color={b.status === 'completed' ? COLORS.success : COLORS.primary} />
          </Card>
        )) : <Text style={styles.emptyText}>No active bookings</Text>}
      </View>

      <View style={[styles.section, { marginBottom: 40 }]}>
        <Text style={styles.sectionTitle}>Booking History ({history.length})</Text>
        {history.length > 0 ? history.slice(0, 5).map((b, i) => (
          <Card key={i}>
            <Text style={styles.bookService}>{b.service}</Text>
            <Text style={styles.bookDetail}>{b.date} at {b.time}</Text>
          </Card>
        )) : <Text style={styles.emptyText}>No completed bookings</Text>}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: { backgroundColor: COLORS.primary, paddingTop: 50, paddingBottom: 30, alignItems: 'center' },
  emoji: { fontSize: 56 },
  name: { fontSize: 26, fontWeight: '700', color: COLORS.white, marginTop: 8 },
  breed: { fontSize: 16, color: 'rgba(255,255,255,0.8)', marginTop: 4 },
  detail: { fontSize: 13, color: 'rgba(255,255,255,0.7)', marginTop: 4 },
  actions: { flexDirection: 'row', justifyContent: 'center', marginTop: -20, marginBottom: 10 },
  actionBtn: { flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.white, borderRadius: RADIUS.full, paddingHorizontal: 20, paddingVertical: 10, marginHorizontal: 8, ...SHADOWS.small },
  actionText: { fontSize: 14, fontWeight: '500', color: COLORS.primary, marginLeft: 6 },
  section: { padding: SPACING.md },
  sectionTitle: { fontSize: 18, fontWeight: '700', color: COLORS.dark, marginBottom: 10 },
  infoRow: { fontSize: 14, color: COLORS.dark, marginBottom: 6 },
  bookService: { fontSize: 15, fontWeight: '600', color: COLORS.dark },
  bookDetail: { fontSize: 13, color: COLORS.grey, marginTop: 2, marginBottom: 6 },
  emptyText: { fontSize: 14, color: COLORS.grey, fontStyle: 'italic' },
  errorText: { fontSize: 16, color: COLORS.danger, textAlign: 'center', marginTop: 40 },
});
