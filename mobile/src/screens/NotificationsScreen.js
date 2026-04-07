import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, FlatList } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import GradientHeader from '../components/GradientHeader';
import EmptyState from '../components/EmptyState';

const MOCK_NOTIFS = [
  { id: 1, type: 'booking', title: 'Booking Confirmed', message: 'Your grooming appointment has been confirmed.', icon: 'check-circle', color: COLORS.success, time: 'Just now' },
  { id: 2, type: 'pickup', title: 'Pet Ready for Pickup', message: 'Your pet is ready for pickup!', icon: 'bell', color: COLORS.warning, time: '5 min ago' },
  { id: 3, type: 'message', title: 'New Message', message: 'You have a new message from a vendor.', icon: 'message-circle', color: COLORS.primary, time: '15 min ago' },
  { id: 4, type: 'promo', title: 'Special Offer', message: '20% off grooming services this weekend!', icon: 'tag', color: COLORS.secondary, time: '1 hour ago' },
  { id: 5, type: 'review', title: 'Review Reminder', message: 'How was your recent grooming session? Leave a review!', icon: 'star', color: COLORS.star, time: '2 hours ago' },
];

export default function NotificationsScreen() {
  const [notifications, setNotifications] = useState(MOCK_NOTIFS);

  return (
    <View style={styles.container}>
      <GradientHeader title="Notifications" subtitle={`${notifications.length} notification${notifications.length !== 1 ? 's' : ''}`} />
      <FlatList data={notifications} keyExtractor={(n) => String(n.id)}
        contentContainerStyle={styles.list}
        ListEmptyComponent={<EmptyState icon="bell-off" title="No notifications" message="You're all caught up!" />}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={[styles.iconBg, { backgroundColor: item.color + '15' }]}>
              <Feather name={item.icon} size={20} color={item.color} />
            </View>
            <View style={styles.cardBody}>
              <Text style={styles.title}>{item.title}</Text>
              <Text style={styles.message}>{item.message}</Text>
              <Text style={styles.time}>{item.time}</Text>
            </View>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  list: { padding: SPACING.md },
  card: { flexDirection: 'row', backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: 14, marginBottom: 8, ...SHADOWS.small },
  iconBg: { width: 42, height: 42, borderRadius: 21, alignItems: 'center', justifyContent: 'center' },
  cardBody: { flex: 1, marginLeft: 12 },
  title: { fontSize: 15, fontWeight: '600', color: COLORS.dark },
  message: { fontSize: 13, color: COLORS.grey, marginTop: 3 },
  time: { fontSize: 11, color: COLORS.textLight, marginTop: 4 },
});
