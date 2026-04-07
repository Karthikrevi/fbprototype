import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { COLORS, SPACING, RADIUS } from '../constants/theme';
import { petsAPI } from '../services/api';
import Input from '../components/Input';
import Button from '../components/Button';
import GradientHeader from '../components/GradientHeader';

export default function EditPetScreen({ route, navigation }) {
  const { pet, petIndex } = route.params;
  const [form, setForm] = useState({ ...pet });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const update = (k, v) => setForm(p => ({ ...p, [k]: v }));

  const handleSave = async () => {
    setLoading(true); setError('');
    try {
      await petsAPI.update(petIndex, form);
      navigation.goBack();
    } catch (e) { setError(e.response?.data?.error || 'Failed to update pet'); }
    finally { setLoading(false); }
  };

  return (
    <View style={styles.container}>
      <GradientHeader title={`Edit ${pet.name}`} />
      <ScrollView contentContainerStyle={styles.form}>
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <Input label="Pet Name" value={form.name} onChangeText={v => update('name', v)} />
        <Input label="Species" value={form.species} onChangeText={v => update('species', v)} />
        <Input label="Breed" value={form.breed} onChangeText={v => update('breed', v)} />
        <Input label="Birthday" value={form.birthday} onChangeText={v => update('birthday', v)} />
        <Input label="Blood Type" value={form.blood} onChangeText={v => update('blood', v)} />
        <Input label="Parent Name" value={form.parent_name} onChangeText={v => update('parent_name', v)} />
        <Input label="Parent Phone" value={form.parent_phone} onChangeText={v => update('parent_phone', v)} keyboardType="phone-pad" />
        <Button title="Save Changes" onPress={handleSave} loading={loading} style={{ marginTop: 8 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  form: { padding: SPACING.lg },
  error: { backgroundColor: '#fde8e8', color: COLORS.danger, padding: 12, borderRadius: RADIUS.sm, marginBottom: SPACING.md, textAlign: 'center' },
});
