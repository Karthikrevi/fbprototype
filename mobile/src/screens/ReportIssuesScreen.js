import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, Alert } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS } from '../constants/theme';
import Button from '../components/Button';
import GradientHeader from '../components/GradientHeader';

const CATEGORIES = [
  { key: 'stray', label: 'Report a Stray Dog', icon: 'map-pin' },
  { key: 'groomer', label: 'Report a Groomer Issue', icon: 'scissors' },
  { key: 'ngo', label: 'Report NGO Discrepancy', icon: 'alert-circle' },
  { key: 'support', label: 'Contact FurrButler Support', icon: 'headphones' },
];

export default function ReportIssuesScreen({ navigation }) {
  const [category, setCategory] = useState('');
  const [description, setDescription] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = () => {
    if (!category || !description.trim()) {
      Alert.alert('Missing Info', 'Please select a category and describe the issue.');
      return;
    }
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.successContainer}>
        <Feather name="check-circle" size={64} color={COLORS.success} />
        <Text style={styles.successTitle}>Report Submitted</Text>
        <Text style={styles.successText}>Thank you for your report. Our team will review it and take appropriate action.</Text>
        <Button title="Back to Home" onPress={() => navigation.navigate('Home')} style={{ marginTop: 24 }} />
      </ScrollView>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <GradientHeader title="Report an Issue" subtitle="Help us improve" />
      <View style={styles.content}>
        <Text style={styles.label}>Select Category</Text>
        {CATEGORIES.map((cat) => (
          <TouchableOpacity key={cat.key} style={[styles.catCard, category === cat.key && styles.catActive]}
            onPress={() => setCategory(cat.key)}>
            <Feather name={cat.icon} size={20} color={category === cat.key ? COLORS.white : COLORS.primary} />
            <Text style={[styles.catLabel, category === cat.key && styles.catLabelActive]}>{cat.label}</Text>
          </TouchableOpacity>
        ))}

        <Text style={styles.label}>Description</Text>
        <TextInput style={styles.textArea} multiline numberOfLines={5} placeholder="Describe the issue in detail..."
          placeholderTextColor={COLORS.grey} value={description} onChangeText={setDescription} textAlignVertical="top" />

        <Button title="Submit Report" onPress={handleSubmit} style={{ marginTop: 16 }} />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: SPACING.lg },
  label: { fontSize: 16, fontWeight: '600', color: COLORS.dark, marginTop: 16, marginBottom: 10 },
  catCard: { flexDirection: 'row', alignItems: 'center', padding: 14, backgroundColor: COLORS.white, borderRadius: RADIUS.md, marginBottom: 8, borderWidth: 1, borderColor: COLORS.border },
  catActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  catLabel: { fontSize: 15, color: COLORS.dark, marginLeft: 12 },
  catLabelActive: { color: COLORS.white, fontWeight: '600' },
  textArea: { backgroundColor: COLORS.white, borderRadius: RADIUS.md, borderWidth: 1, borderColor: COLORS.border, padding: 14, fontSize: 15, color: COLORS.dark, minHeight: 120 },
  successContainer: { flexGrow: 1, justifyContent: 'center', alignItems: 'center', padding: SPACING.xl },
  successTitle: { fontSize: 22, fontWeight: '700', color: COLORS.dark, marginTop: 16 },
  successText: { fontSize: 14, color: COLORS.grey, textAlign: 'center', marginTop: 8 },
});
