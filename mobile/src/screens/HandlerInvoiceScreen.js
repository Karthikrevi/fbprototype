import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import Card from '../components/Card';
import Button from '../components/Button';

export default function HandlerInvoiceScreen({ route, navigation }) {
  const { booking } = route.params || {};

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.successIcon}>
        <Feather name="check-circle" size={64} color={COLORS.success} />
      </View>
      <Text style={styles.title}>Booking Confirmed</Text>
      <Text style={styles.subtitle}>Your handler booking has been placed</Text>

      <Card style={styles.invoice}>
        <Text style={styles.invoiceTitle}>Booking Details</Text>
        {booking && (
          <>
            <View style={styles.row}><Text style={styles.label}>Booking ID</Text><Text style={styles.value}>{booking.id}</Text></View>
            <View style={styles.row}><Text style={styles.label}>Pet</Text><Text style={styles.value}>{booking.pet_name}</Text></View>
            <View style={styles.row}><Text style={styles.label}>Destination</Text><Text style={styles.value}>{booking.destination}</Text></View>
            <View style={styles.row}><Text style={styles.label}>Travel Date</Text><Text style={styles.value}>{booking.travel_date}</Text></View>
            <View style={styles.row}><Text style={styles.label}>Status</Text><Text style={styles.value}>{booking.status}</Text></View>
            <View style={styles.row}><Text style={styles.label}>Payment</Text><Text style={styles.value}>Escrow (held until delivery)</Text></View>
          </>
        )}
      </Card>

      <Button title="View My Bookings" onPress={() => navigation.navigate('MyHandlerBookings')} style={{ marginTop: 20 }} />
      <Button title="Back to Home" variant="outline" onPress={() => navigation.navigate('Home')} style={{ marginTop: 10 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: SPACING.lg, alignItems: 'center' },
  successIcon: { marginTop: 30, marginBottom: 16 },
  title: { fontSize: 24, fontWeight: '700', color: COLORS.dark },
  subtitle: { fontSize: 14, color: COLORS.grey, marginTop: 6 },
  invoice: { width: '100%', marginTop: 24 },
  invoiceTitle: { fontSize: 18, fontWeight: '600', color: COLORS.dark, marginBottom: 12 },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: COLORS.lightGrey },
  label: { fontSize: 14, color: COLORS.grey },
  value: { fontSize: 14, fontWeight: '500', color: COLORS.dark },
});
