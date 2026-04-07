import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { petsAPI } from '../services/api';
import Card from '../components/Card';
import GradientHeader from '../components/GradientHeader';
import LoadingScreen from '../components/LoadingScreen';

export default function PassportScreen({ route }) {
  const { petIndex } = route.params;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { const res = await petsAPI.passport(petIndex); setData(res.data); }
      catch {} finally { setLoading(false); }
    })();
  }, [petIndex]);

  if (loading) return <LoadingScreen />;

  const docs = data?.documents || [];
  const required = data?.required_docs || {};
  const pct = data?.completion_pct || 0;

  const getDocStatus = (type) => {
    const doc = docs.find(d => d.doc_type === type && d.status === 'approved');
    return doc ? 'approved' : docs.find(d => d.doc_type === type) ? 'pending' : 'missing';
  };

  return (
    <ScrollView style={styles.container}>
      <GradientHeader title="Pet Passport" subtitle={`${pct}% Complete`} />
      <View style={styles.progressBar}>
        <View style={[styles.progressFill, { width: `${pct}%` }]} />
      </View>
      <View style={styles.content}>
        {Object.entries(required).map(([key, info]) => {
          const status = getDocStatus(key);
          const icon = status === 'approved' ? 'check-circle' : status === 'pending' ? 'clock' : 'circle';
          const color = status === 'approved' ? COLORS.success : status === 'pending' ? COLORS.warning : COLORS.grey;
          return (
            <Card key={key}>
              <View style={styles.docRow}>
                <Feather name={icon} size={22} color={color} />
                <View style={styles.docInfo}>
                  <Text style={styles.docName}>{info.name}</Text>
                  <Text style={styles.docMeta}>
                    {status === 'approved' ? 'Approved' : status === 'pending' ? 'Pending review' : 'Not uploaded'}
                    {' • Can be uploaded by: '}{info.allowed_roles.join(', ')}
                  </Text>
                </View>
              </View>
            </Card>
          );
        })}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: SPACING.md },
  progressBar: { height: 6, backgroundColor: COLORS.lightGrey, marginHorizontal: SPACING.md, borderRadius: 3, marginTop: SPACING.sm },
  progressFill: { height: 6, backgroundColor: COLORS.success, borderRadius: 3 },
  docRow: { flexDirection: 'row', alignItems: 'center' },
  docInfo: { marginLeft: 14, flex: 1 },
  docName: { fontSize: 15, fontWeight: '600', color: COLORS.dark },
  docMeta: { fontSize: 12, color: COLORS.grey, marginTop: 3 },
});
