import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Image } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { vendorAPI } from '../services/api';
import Card from '../components/Card';
import Badge from '../components/Badge';
import StarRating from '../components/StarRating';
import Button from '../components/Button';
import LoadingScreen from '../components/LoadingScreen';

export default function VendorProfileScreen({ route, navigation }) {
  const { vendorId } = route.params;
  const [vendor, setVendor] = useState(null);
  const [services, setServices] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [groomers, setGroomers] = useState([]);
  const [hasProducts, setHasProducts] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [vRes, gRes] = await Promise.all([vendorAPI.profile(vendorId), vendorAPI.groomers(vendorId)]);
        setVendor(vRes.data.vendor);
        setServices(vRes.data.services || []);
        setReviews(vRes.data.reviews || []);
        setHasProducts(vRes.data.has_products);
        setGroomers(gRes.data.groomers || []);
      } catch {} finally { setLoading(false); }
    })();
  }, [vendorId]);

  if (loading) return <LoadingScreen />;
  if (!vendor) return <View style={styles.container}><Text>Vendor not found</Text></View>;

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.name}>{vendor.name}</Text>
        <View style={styles.ratingRow}>
          <StarRating rating={Math.round(vendor.rating)} size={18} />
          <Text style={styles.ratingText}>{vendor.rating} ({vendor.total_reviews} reviews)</Text>
        </View>
        <Text style={styles.category}>{vendor.category} • {vendor.city}</Text>
        {vendor.is_online ? <Badge text="Online" color={COLORS.success} /> : <Badge text="Offline" color={COLORS.grey} />}
      </View>

      {vendor.description ? <Text style={styles.bio}>{vendor.description}</Text> : null}

      <View style={styles.actionRow}>
        <Button title="Book Now" onPress={() => navigation.navigate('Booking', { vendorId })} style={styles.actionBtn} />
        {hasProducts && <Button title="Shop" variant="outline" onPress={() => navigation.navigate('VendorShop', { vendorId })} style={styles.actionBtn} />}
        <Button title="Chat" variant="secondary" onPress={() => navigation.navigate('Conversations', { startWith: vendorId })} style={styles.actionBtn} />
      </View>

      {services.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Services</Text>
          {services.map((s, i) => (
            <Card key={i}>
              <Text style={styles.serviceName}>{s.name}</Text>
              <Text style={styles.serviceDesc}>{s.description}</Text>
              <View style={styles.serviceFooter}>
                <Text style={styles.servicePrice}>${s.price}</Text>
                <Text style={styles.serviceDuration}>{s.duration} min</Text>
              </View>
            </Card>
          ))}
        </View>
      )}

      {groomers.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Our Team</Text>
          {groomers.map((g) => (
            <Card key={g.id} onPress={() => navigation.navigate('GroomerProfile', { employeeId: g.id })}>
              <View style={styles.groomerRow}>
                <Text style={styles.groomerName}>{g.name}</Text>
                {g.is_certified ? <Badge text="Certified" color={COLORS.success} /> : null}
                {g.is_groomer_of_month ? <Badge text="⭐ GOTM" color={COLORS.warning} /> : null}
              </View>
              <Text style={styles.groomerMeta}>{g.position} • ⭐ {g.avg_rating} ({g.total_reviews} reviews)</Text>
            </Card>
          ))}
        </View>
      )}

      <View style={[styles.section, { marginBottom: 40 }]}>
        <Text style={styles.sectionTitle}>Reviews ({reviews.length})</Text>
        {reviews.length > 0 ? reviews.slice(0, 10).map((r, i) => (
          <Card key={i}>
            <View style={styles.reviewHeader}>
              <StarRating rating={r.rating} size={14} />
              <Text style={styles.reviewDate}>{r.timestamp?.split(' ')[0]}</Text>
            </View>
            <Text style={styles.reviewText}>{r.review_text || 'No comment'}</Text>
            <Text style={styles.reviewMeta}>{r.service_type} • by {r.user_email}</Text>
          </Card>
        )) : <Text style={styles.emptyText}>No reviews yet</Text>}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: { backgroundColor: COLORS.primary, paddingTop: 50, paddingBottom: 24, paddingHorizontal: SPACING.lg },
  name: { fontSize: 24, fontWeight: '700', color: COLORS.white },
  ratingRow: { flexDirection: 'row', alignItems: 'center', marginTop: 8 },
  ratingText: { fontSize: 14, color: 'rgba(255,255,255,0.9)', marginLeft: 8 },
  category: { fontSize: 14, color: 'rgba(255,255,255,0.8)', marginTop: 6, marginBottom: 8 },
  bio: { fontSize: 14, color: COLORS.dark, padding: SPACING.md, lineHeight: 20 },
  actionRow: { flexDirection: 'row', paddingHorizontal: SPACING.md, paddingVertical: SPACING.sm },
  actionBtn: { flex: 1, marginHorizontal: 4 },
  section: { paddingHorizontal: SPACING.md, marginTop: SPACING.sm },
  sectionTitle: { fontSize: 18, fontWeight: '700', color: COLORS.dark, marginBottom: 10 },
  serviceName: { fontSize: 15, fontWeight: '600', color: COLORS.dark },
  serviceDesc: { fontSize: 13, color: COLORS.grey, marginTop: 4 },
  serviceFooter: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 8 },
  servicePrice: { fontSize: 16, fontWeight: '700', color: COLORS.primary },
  serviceDuration: { fontSize: 13, color: COLORS.grey },
  groomerRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  groomerName: { fontSize: 15, fontWeight: '600', color: COLORS.dark },
  groomerMeta: { fontSize: 12, color: COLORS.grey, marginTop: 4 },
  reviewHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  reviewDate: { fontSize: 12, color: COLORS.grey },
  reviewText: { fontSize: 14, color: COLORS.dark, marginTop: 6 },
  reviewMeta: { fontSize: 12, color: COLORS.grey, marginTop: 4 },
  emptyText: { fontSize: 14, color: COLORS.grey, fontStyle: 'italic' },
});
