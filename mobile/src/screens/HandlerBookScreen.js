import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { COLORS, SPACING, RADIUS } from '../constants/theme';
import { handlersAPI, petsAPI } from '../services/api';
import Input from '../components/Input';
import Button from '../components/Button';
import GradientHeader from '../components/GradientHeader';

export default function HandlerBookScreen({ route, navigation }) {
  const { handlerId, handler } = route.params;
  const [pets, setPets] = useState([]);
  const [form, setForm] = useState({ pet_name: '', travel_date: '', destination: '', notes: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    (async () => { try { const res = await petsAPI.list(); setPets(res.data.pets || []); } catch {} })();
  }, []);

  const update = (k, v) => setForm(p => ({ ...p, [k]: v }));

  const handleBook = async () => {
    if (!form.pet_name || !form.travel_date || !form.destination) { setError('Please fill all required fields'); return; }
    setLoading(true); setError('');
    try {
      const res = await handlersAPI.book(handlerId, form);
      setSuccess('Booking confirmed! Invoice sent.');
      setTimeout(() => navigation.navigate('HandlerInvoice', { booking: res.data.booking }), 1500);
    } catch (e) { setError(e.response?.data?.error || 'Booking failed'); }
    finally { setLoading(false); }
  };

  return (
    <ScrollView style={styles.container}>
      <GradientHeader title="Book Handler" subtitle={handler?.name} />
      <View style={styles.content}>
        {error ? <Text style={styles.error}>{error}</Text> : null}
        {success ? <Text style={styles.success}>{success}</Text> : null}
        <Input label="Pet Name *" placeholder="Select pet" value={form.pet_name} onChangeText={v => update('pet_name', v)} />
        <Input label="Travel Date *" placeholder="YYYY-MM-DD" value={form.travel_date} onChangeText={v => update('travel_date', v)} />
        <Input label="Destination *" placeholder="City, Country" value={form.destination} onChangeText={v => update('destination', v)} />
        <Input label="Notes" placeholder="Special requirements..." value={form.notes} onChangeText={v => update('notes', v)} multiline numberOfLines={3} />
        <Button title="Confirm Booking" onPress={handleBook} loading={loading} style={{ marginTop: 12 }} />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: SPACING.lg },
  error: { backgroundColor: '#fde8e8', color: COLORS.danger, padding: 12, borderRadius: RADIUS.sm, textAlign: 'center', marginBottom: 12 },
  success: { backgroundColor: '#d4edda', color: COLORS.success, padding: 12, borderRadius: RADIUS.sm, textAlign: 'center', marginBottom: 12 },
});
