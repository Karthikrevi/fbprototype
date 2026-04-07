import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { vendorAPI, petsAPI, bookingsAPI } from '../services/api';
import Button from '../components/Button';
import GradientHeader from '../components/GradientHeader';
import LoadingScreen from '../components/LoadingScreen';

export default function BookingScreen({ route, navigation }) {
  const { vendorId } = route.params;
  const [vendor, setVendor] = useState(null);
  const [services, setServices] = useState([]);
  const [groomers, setGroomers] = useState([]);
  const [pets, setPets] = useState([]);
  const [slots, setSlots] = useState([]);
  const [sel, setSel] = useState({ service: '', groomer: null, pet: '', date: '', time: '' });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const [vRes, gRes, pRes] = await Promise.all([
          vendorAPI.profile(vendorId), vendorAPI.groomers(vendorId), petsAPI.list()
        ]);
        setVendor(vRes.data.vendor);
        setServices(vRes.data.services || []);
        setGroomers(gRes.data.groomers || []);
        setPets(pRes.data.pets || []);
      } catch {} finally { setLoading(false); }
    })();
  }, [vendorId]);

  const loadSlots = async (date) => {
    setSel(p => ({ ...p, date, time: '' }));
    try { const res = await vendorAPI.slots(vendorId, date); setSlots(res.data.slots || []); } catch { setSlots([]); }
  };

  const handleBook = async () => {
    if (!sel.service || !sel.pet || !sel.date || !sel.time) { setError('Please fill all fields'); return; }
    setSubmitting(true); setError('');
    try {
      const pet = pets.find(p => p.name === sel.pet);
      await bookingsAPI.create({
        vendor_id: vendorId, service: sel.service, date: sel.date, time: sel.time,
        pet_name: sel.pet, pet_parent_name: pet?.parent_name || '',
        pet_parent_phone: pet?.parent_phone || '', employee_id: sel.groomer || undefined,
        duration: services.find(s => s.name === sel.service)?.duration || 30,
      });
      setSuccess('Booking confirmed!');
      setTimeout(() => navigation.goBack(), 1500);
    } catch (e) { setError(e.response?.data?.error || 'Booking failed'); }
    finally { setSubmitting(false); }
  };

  if (loading) return <LoadingScreen />;

  const today = new Date().toISOString().split('T')[0];
  const dates = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(); d.setDate(d.getDate() + i);
    return d.toISOString().split('T')[0];
  });

  return (
    <ScrollView style={styles.container}>
      <GradientHeader title="Book Appointment" subtitle={vendor?.name} />
      <View style={styles.content}>
        {error ? <Text style={styles.error}>{error}</Text> : null}
        {success ? <Text style={styles.success}>{success}</Text> : null}

        <Text style={styles.label}>Select Service</Text>
        <View style={styles.chips}>
          {services.map((s, i) => (
            <TouchableOpacity key={i} style={[styles.chip, sel.service === s.name && styles.chipActive]}
              onPress={() => setSel(p => ({ ...p, service: s.name }))}>
              <Text style={[styles.chipText, sel.service === s.name && styles.chipTextActive]}>{s.name} - ${s.price}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.label}>Select Pet</Text>
        <View style={styles.chips}>
          {pets.map((p, i) => (
            <TouchableOpacity key={i} style={[styles.chip, sel.pet === p.name && styles.chipActive]}
              onPress={() => setSel(prev => ({ ...prev, pet: p.name }))}>
              <Text style={[styles.chipText, sel.pet === p.name && styles.chipTextActive]}>{p.name}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {groomers.length > 0 && (
          <>
            <Text style={styles.label}>Select Groomer (optional)</Text>
            <View style={styles.chips}>
              {groomers.map((g) => (
                <TouchableOpacity key={g.id} style={[styles.chip, sel.groomer === g.id && styles.chipActive]}
                  onPress={() => setSel(p => ({ ...p, groomer: g.id }))}>
                  <Text style={[styles.chipText, sel.groomer === g.id && styles.chipTextActive]}>{g.name}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </>
        )}

        <Text style={styles.label}>Select Date</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.dateScroll}>
          {dates.map((d) => {
            const day = new Date(d); const dn = day.toLocaleDateString('en', { weekday: 'short' });
            return (
              <TouchableOpacity key={d} style={[styles.dateChip, sel.date === d && styles.dateChipActive]}
                onPress={() => loadSlots(d)}>
                <Text style={[styles.dateDay, sel.date === d && styles.dateTextActive]}>{dn}</Text>
                <Text style={[styles.dateNum, sel.date === d && styles.dateTextActive]}>{day.getDate()}</Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {sel.date ? (
          <>
            <Text style={styles.label}>Select Time</Text>
            <View style={styles.chips}>
              {slots.length > 0 ? slots.map((s, i) => (
                <TouchableOpacity key={i} style={[styles.timeChip, sel.time === s && styles.chipActive]}
                  onPress={() => setSel(p => ({ ...p, time: s }))}>
                  <Text style={[styles.chipText, sel.time === s && styles.chipTextActive]}>{s}</Text>
                </TouchableOpacity>
              )) : <Text style={styles.emptyText}>No slots available for this date</Text>}
            </View>
          </>
        ) : null}

        <Button title="Confirm Booking" onPress={handleBook} loading={submitting} style={{ marginTop: 20 }} />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: SPACING.lg },
  label: { fontSize: 16, fontWeight: '600', color: COLORS.dark, marginTop: 16, marginBottom: 8 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 10, borderRadius: RADIUS.full, backgroundColor: COLORS.white, borderWidth: 1, borderColor: COLORS.border },
  chipActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  chipText: { fontSize: 13, color: COLORS.dark },
  chipTextActive: { color: COLORS.white, fontWeight: '600' },
  dateScroll: { marginBottom: 8 },
  dateChip: { width: 60, height: 70, borderRadius: RADIUS.md, backgroundColor: COLORS.white, marginRight: 8, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: COLORS.border },
  dateChipActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  dateDay: { fontSize: 12, color: COLORS.grey },
  dateNum: { fontSize: 20, fontWeight: '700', color: COLORS.dark },
  dateTextActive: { color: COLORS.white },
  timeChip: { paddingHorizontal: 16, paddingVertical: 10, borderRadius: RADIUS.sm, backgroundColor: COLORS.white, borderWidth: 1, borderColor: COLORS.border },
  error: { backgroundColor: '#fde8e8', color: COLORS.danger, padding: 12, borderRadius: RADIUS.sm, textAlign: 'center', marginBottom: 8 },
  success: { backgroundColor: '#d4edda', color: COLORS.success, padding: 12, borderRadius: RADIUS.sm, textAlign: 'center', marginBottom: 8 },
  emptyText: { fontSize: 14, color: COLORS.grey, fontStyle: 'italic' },
});
