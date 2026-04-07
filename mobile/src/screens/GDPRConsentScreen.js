import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS } from '../constants/theme';
import Button from '../components/Button';
import api from '../services/api';

export default function GDPRConsentScreen({ onAccept }) {
  const [tos, setTos] = useState(false);
  const [privacy, setPrivacy] = useState(false);
  const [promo, setPromo] = useState(false);
  const [analytics, setAnalytics] = useState(false);

  const canContinue = tos && privacy;

  const handleAccept = async () => {
    const consent = { tos: true, privacy: true, promo, analytics, accepted_at: new Date().toISOString() };
    await AsyncStorage.setItem('gdpr_accepted', JSON.stringify(consent));
    try { await api.post('/auth/gdpr-consent', consent); } catch {}
    onAccept?.();
  };

  const Checkbox = ({ checked, onToggle, label, required }) => (
    <TouchableOpacity style={styles.checkRow} onPress={onToggle} activeOpacity={0.7}>
      <Feather name={checked ? 'check-square' : 'square'} size={22} color={checked ? COLORS.primary : COLORS.grey} />
      <Text style={styles.checkLabel}>
        {label}{required ? <Text style={styles.required}> *</Text> : ''}
      </Text>
    </TouchableOpacity>
  );

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.emoji}>🔒</Text>
      <Text style={styles.title}>Your Privacy Matters</Text>
      <Text style={styles.subtitle}>Before you begin, please review our data practices</Text>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>What data we collect</Text>
        <Text style={styles.text}>• Your email and name for account management{'\n'}• Pet information you provide{'\n'}• Location data when searching for services{'\n'}• Booking and order history</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>How we use it</Text>
        <Text style={styles.text}>• To provide grooming, marketplace and travel services{'\n'}• To match you with nearby vendors{'\n'}• To improve service quality through anonymous analytics</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Your rights under GDPR</Text>
        <Text style={styles.text}>• Access all data we hold about you{'\n'}• Request correction of inaccurate data{'\n'}• Request deletion of your account and data{'\n'}• Withdraw consent at any time via Settings</Text>
      </View>

      <View style={styles.checkboxes}>
        <Checkbox checked={tos} onToggle={() => setTos(!tos)} label="I agree to the Terms of Service" required />
        <Checkbox checked={privacy} onToggle={() => setPrivacy(!privacy)} label="I agree to the Privacy Policy" required />
        <Checkbox checked={promo} onToggle={() => setPromo(!promo)} label="Receive promotional messages from vendors I book with" />
        <Checkbox checked={analytics} onToggle={() => setAnalytics(!analytics)} label="Share anonymous usage data to improve the app" />
      </View>

      <Button title="Accept and Continue" onPress={handleAccept} disabled={!canContinue} style={{ marginTop: 24 }} />
      <Text style={styles.footnote}>* Required</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: SPACING.lg, paddingTop: 60 },
  emoji: { fontSize: 48, textAlign: 'center' },
  title: { fontSize: 24, fontWeight: '700', color: COLORS.dark, textAlign: 'center', marginTop: 12 },
  subtitle: { fontSize: 14, color: COLORS.grey, textAlign: 'center', marginTop: 6, marginBottom: 24 },
  section: { marginBottom: 20 },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: COLORS.dark, marginBottom: 8 },
  text: { fontSize: 14, color: COLORS.dark, lineHeight: 22 },
  checkboxes: { marginTop: 16, borderTopWidth: 1, borderTopColor: COLORS.lightGrey, paddingTop: 16 },
  checkRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10 },
  checkLabel: { fontSize: 14, color: COLORS.dark, marginLeft: 12, flex: 1 },
  required: { color: COLORS.danger },
  footnote: { textAlign: 'center', fontSize: 12, color: COLORS.grey, marginTop: 12 },
});
