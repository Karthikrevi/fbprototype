import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Alert } from 'react-native';
import { COLORS, SPACING, RADIUS } from '../constants/theme';
import { petsAPI } from '../services/api';
import Input from '../components/Input';
import Button from '../components/Button';
import GradientHeader from '../components/GradientHeader';

export default function AddPetScreen({ navigation }) {
  const [form, setForm] = useState({ name: '', species: 'Dog', breed: '', birthday: '', blood: '', parent_name: '', parent_phone: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const update = (k, v) => setForm(p => ({ ...p, [k]: v }));

  const handleSave = async () => {
    if (!form.name) { setError('Pet name is required'); return; }
    setLoading(true); setError('');
    try {
      await petsAPI.add(form);
      navigation.goBack();
    } catch (e) { setError(e.response?.data?.error || 'Failed to add pet'); }
    finally { setLoading(false); }
  };

  return (
    <View style={styles.container}>
      <GradientHeader title="Add New Pet" />
      <ScrollView contentContainerStyle={styles.form}>
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <Input label="Pet Name *" placeholder="e.g. Buddy" value={form.name} onChangeText={v => update('name', v)} />
        <Input label="Species" placeholder="Dog, Cat, etc." value={form.species} onChangeText={v => update('species', v)} />
        <Input label="Breed" placeholder="e.g. Labrador" value={form.breed} onChangeText={v => update('breed', v)} />
        <Input label="Birthday" placeholder="YYYY-MM-DD" value={form.birthday} onChangeText={v => update('birthday', v)} />
        <Input label="Blood Type" placeholder="e.g. DEA 1.1+" value={form.blood} onChangeText={v => update('blood', v)} />
        <Input label="Parent Name" placeholder="Your name" value={form.parent_name} onChangeText={v => update('parent_name', v)} />
        <Input label="Parent Phone" placeholder="Phone number" value={form.parent_phone} onChangeText={v => update('parent_phone', v)} keyboardType="phone-pad" />
        <Button title="Add Pet" onPress={handleSave} loading={loading} style={{ marginTop: 8 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  form: { padding: SPACING.lg },
  error: { backgroundColor: '#fde8e8', color: COLORS.danger, padding: 12, borderRadius: RADIUS.sm, marginBottom: SPACING.md, textAlign: 'center' },
});
