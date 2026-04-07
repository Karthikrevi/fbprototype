import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { COLORS, SPACING, RADIUS } from '../constants/theme';
import { groomerAPI } from '../services/api';
import Card from '../components/Card';
import Badge from '../components/Badge';
import StarRating from '../components/StarRating';
import LoadingScreen from '../components/LoadingScreen';

export default function GroomerProfileScreen({ route }) {
  const { employeeId } = route.params;
  const [groomer, setGroomer] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [vendor, setVendor] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await groomerAPI.profile(employeeId);
        setGroomer(res.data.groomer); setReviews(res.data.reviews || []); setVendor(res.data.vendor);
      } catch {} finally { setLoading(false); }
    })();
  }, [employeeId]);

  if (loading) return <LoadingScreen />;
  if (!groomer) return <View style={styles.container}><Text>Groomer not found</Text></View>;

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.name}>{groomer.name}</Text>
        <Text style={styles.position}>{groomer.position}</Text>
        {vendor && <Text style={styles.vendorInfo}>{vendor.name} • {vendor.city}</Text>}
        <View style={styles.badges}>
          {groomer.is_certified ? <Badge text="✅ Certified Groomer" color={COLORS.success} /> : null}
          {groomer.is_groomer_of_month ? <Badge text="⭐ Groomer of the Month" color={COLORS.warning} /> : null}
        </View>
      </View>

      <View style={styles.statsGrid}>
        <View style={styles.statBox}>
          <Text style={styles.statValue}>{groomer.avg_rating?.toFixed(1) || 0}</Text>
          <Text style={styles.statLabel}>Rating</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={styles.statValue}>{groomer.total_reviews}</Text>
          <Text style={styles.statLabel}>Reviews</Text>
        </View>
      </View>

      <View style={[styles.section, { marginBottom: 40 }]}>
        <Text style={styles.sectionTitle}>Reviews</Text>
        {reviews.map((r, i) => (
          <Card key={i}>
            <View style={styles.reviewHeader}>
              <StarRating rating={r.rating} size={14} />
              <Text style={styles.reviewDate}>{r.created_at?.split(' ')[0]}</Text>
            </View>
            <Text style={styles.reviewText}>{r.review_text || 'No comment'}</Text>
            {r.would_book_again ? <Text style={styles.bookAgain}>Would book again ✓</Text> : null}
          </Card>
        ))}
        {reviews.length === 0 && <Text style={styles.emptyText}>No reviews yet</Text>}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: { backgroundColor: COLORS.primary, paddingTop: 50, paddingBottom: 24, paddingHorizontal: SPACING.lg },
  name: { fontSize: 24, fontWeight: '700', color: COLORS.white },
  position: { fontSize: 15, color: 'rgba(255,255,255,0.8)', marginTop: 4 },
  vendorInfo: { fontSize: 13, color: 'rgba(255,255,255,0.7)', marginTop: 4 },
  badges: { flexDirection: 'row', gap: 8, marginTop: 10 },
  statsGrid: { flexDirection: 'row', padding: SPACING.md },
  statBox: { flex: 1, backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: SPACING.md, alignItems: 'center', marginHorizontal: 4 },
  statValue: { fontSize: 24, fontWeight: '700', color: COLORS.primary },
  statLabel: { fontSize: 12, color: COLORS.grey, marginTop: 4 },
  section: { paddingHorizontal: SPACING.md, marginTop: SPACING.sm },
  sectionTitle: { fontSize: 18, fontWeight: '700', color: COLORS.dark, marginBottom: 10 },
  reviewHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  reviewDate: { fontSize: 12, color: COLORS.grey },
  reviewText: { fontSize: 14, color: COLORS.dark, marginTop: 6 },
  bookAgain: { fontSize: 12, color: COLORS.success, marginTop: 4 },
  emptyText: { fontSize: 14, color: COLORS.grey, fontStyle: 'italic' },
});
