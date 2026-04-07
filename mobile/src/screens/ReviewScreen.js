import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TextInput, Switch } from 'react-native';
import { COLORS, SPACING, RADIUS } from '../constants/theme';
import { bookingsAPI } from '../services/api';
import StarRating from '../components/StarRating';
import Button from '../components/Button';
import GradientHeader from '../components/GradientHeader';

export default function ReviewScreen({ route, navigation }) {
  const { bookingId } = route.params;
  const [ratings, setRatings] = useState({ cleanliness: 0, service: 0, behavior: 0, overall: 0 });
  const [text, setText] = useState('');
  const [wouldBookAgain, setWouldBookAgain] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const updateRating = (key, val) => setRatings(p => ({ ...p, [key]: val }));

  const handleSubmit = async () => {
    if (!ratings.overall) { setError('Please set at least the overall rating'); return; }
    setLoading(true); setError('');
    try {
      await bookingsAPI.review(bookingId, {
        ...ratings, review_text: text, would_book_again: wouldBookAgain,
      });
      setSuccess('Review submitted! Thank you.');
      setTimeout(() => navigation.goBack(), 1500);
    } catch (e) { setError(e.response?.data?.error || 'Failed to submit review'); }
    finally { setLoading(false); }
  };

  return (
    <ScrollView style={styles.container}>
      <GradientHeader title="Leave a Review" />
      <View style={styles.content}>
        {error ? <Text style={styles.error}>{error}</Text> : null}
        {success ? <Text style={styles.success}>{success}</Text> : null}

        {['cleanliness', 'service', 'behavior', 'overall'].map((cat) => (
          <View key={cat} style={styles.ratingRow}>
            <Text style={styles.ratingLabel}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</Text>
            <StarRating rating={ratings[cat]} editable onRate={(v) => updateRating(cat, v)} size={28} />
          </View>
        ))}

        <Text style={styles.label}>Your Review</Text>
        <TextInput style={styles.textInput} multiline numberOfLines={4}
          placeholder="Share your experience..." placeholderTextColor={COLORS.grey}
          value={text} onChangeText={setText} textAlignVertical="top" />

        <View style={styles.switchRow}>
          <Text style={styles.switchLabel}>Would you book again?</Text>
          <Switch value={wouldBookAgain} onValueChange={setWouldBookAgain}
            trackColor={{ true: COLORS.primary }} thumbColor={COLORS.white} />
        </View>

        <Button title="Submit Review" onPress={handleSubmit} loading={loading} style={{ marginTop: 20 }} />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: SPACING.lg },
  ratingRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: COLORS.lightGrey },
  ratingLabel: { fontSize: 16, fontWeight: '500', color: COLORS.dark },
  label: { fontSize: 16, fontWeight: '600', color: COLORS.dark, marginTop: 20, marginBottom: 8 },
  textInput: { backgroundColor: COLORS.white, borderRadius: RADIUS.sm, borderWidth: 1, borderColor: COLORS.border, padding: 14, fontSize: 15, color: COLORS.dark, minHeight: 100 },
  switchRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 20 },
  switchLabel: { fontSize: 15, color: COLORS.dark },
  error: { backgroundColor: '#fde8e8', color: COLORS.danger, padding: 12, borderRadius: RADIUS.sm, textAlign: 'center', marginBottom: 12 },
  success: { backgroundColor: '#d4edda', color: COLORS.success, padding: 12, borderRadius: RADIUS.sm, textAlign: 'center', marginBottom: 12 },
});
