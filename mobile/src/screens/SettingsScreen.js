import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, Switch, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import Card from '../components/Card';
import Button from '../components/Button';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function SettingsScreen({ navigation }) {
  const { logout, user } = useAuth();
  const [marketingOpt, setMarketingOpt] = useState(false);
  const [dataSharing, setDataSharing] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const consent = JSON.parse(await AsyncStorage.getItem('gdpr_accepted') || '{}');
        setMarketingOpt(consent.promo || false);
        setDataSharing(consent.analytics || false);
      } catch {}
    })();
  }, []);

  const updateConsent = async (key, value) => {
    try {
      const consent = JSON.parse(await AsyncStorage.getItem('gdpr_accepted') || '{}');
      consent[key] = value;
      await AsyncStorage.setItem('gdpr_accepted', JSON.stringify(consent));
    } catch {}
  };

  const handleDownloadData = async () => {
    try {
      const res = await api.get('/gdpr/export-data');
      if (res.data?.success) {
        Alert.alert('Your Data', JSON.stringify(res.data.data, null, 2).substring(0, 500) + '\n\n(Full data available via web portal)');
      } else {
        Alert.alert('Download My Data', 'Your data export request has been submitted. Check the web portal to download.');
      }
    } catch {
      Alert.alert('Download My Data', 'Visit the web portal Settings page to download your full data export.');
    }
  };

  const handleDeleteAccount = () => {
    Alert.alert(
      'Delete Account',
      'Are you sure you want to delete your account? This action cannot be undone and all your data will be permanently removed.',
      [{ text: 'Cancel', style: 'cancel' }, { text: 'Delete', style: 'destructive', onPress: async () => {
        try { await api.post('/gdpr/delete-account'); } catch {}
        await logout();
      }}]
    );
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Settings</Text>
      </View>
      <View style={styles.content}>
        <Text style={styles.sectionTitle}>Account</Text>
        <Card>
          <Text style={styles.infoLabel}>Email</Text>
          <Text style={styles.infoValue}>{user?.email}</Text>
          <Text style={styles.infoLabel}>Name</Text>
          <Text style={styles.infoValue}>{user?.name || 'Not set'}</Text>
        </Card>

        <Text style={styles.sectionTitle}>Privacy Settings</Text>
        <Card>
          <View style={styles.switchRow}>
            <View style={styles.switchInfo}>
              <Text style={styles.switchLabel}>Marketing Communications</Text>
              <Text style={styles.switchDesc}>Receive promotional messages from vendors</Text>
            </View>
            <Switch value={marketingOpt} onValueChange={(v) => { setMarketingOpt(v); updateConsent('promo', v); }}
              trackColor={{ true: COLORS.primary }} thumbColor={COLORS.white} />
          </View>
          <View style={styles.divider} />
          <View style={styles.switchRow}>
            <View style={styles.switchInfo}>
              <Text style={styles.switchLabel}>Data Sharing</Text>
              <Text style={styles.switchDesc}>Share anonymous usage data to improve the app</Text>
            </View>
            <Switch value={dataSharing} onValueChange={(v) => { setDataSharing(v); updateConsent('analytics', v); }}
              trackColor={{ true: COLORS.primary }} thumbColor={COLORS.white} />
          </View>
        </Card>

        <Text style={styles.sectionTitle}>Data Management</Text>
        <Card>
          <Button title="Download My Data" variant="outline" onPress={handleDownloadData} style={{ marginBottom: 10 }} />
          <Button title="Delete Account" variant="danger" onPress={handleDeleteAccount} />
        </Card>

        <Button title="Sign Out" variant="outline" onPress={logout} style={{ marginTop: 24 }} />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: { backgroundColor: COLORS.primary, paddingTop: 50, paddingBottom: 20, paddingHorizontal: SPACING.lg },
  title: { fontSize: 24, fontWeight: '700', color: COLORS.white },
  content: { padding: SPACING.md, paddingBottom: 40 },
  sectionTitle: { fontSize: 18, fontWeight: '700', color: COLORS.dark, marginTop: 20, marginBottom: 10 },
  infoLabel: { fontSize: 12, color: COLORS.grey, marginTop: 8 },
  infoValue: { fontSize: 15, fontWeight: '500', color: COLORS.dark, marginTop: 2 },
  switchRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8 },
  switchInfo: { flex: 1 },
  switchLabel: { fontSize: 15, fontWeight: '500', color: COLORS.dark },
  switchDesc: { fontSize: 12, color: COLORS.grey, marginTop: 2 },
  divider: { height: 1, backgroundColor: COLORS.lightGrey, marginVertical: 8 },
});
