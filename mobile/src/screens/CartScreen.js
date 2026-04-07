import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { ordersAPI } from '../services/api';
import Button from '../components/Button';
import GradientHeader from '../components/GradientHeader';

export default function CartScreen({ route, navigation }) {
  const { cart: initialCart, vendorId, vendorName } = route.params;
  const [cart, setCart] = useState(initialCart);
  const [deliveryType, setDeliveryType] = useState('pickup');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const updateQty = (id, delta) => {
    setCart(prev => prev.map(i => i.id === id ? { ...i, qty: Math.max(0, i.qty + delta) } : i).filter(i => i.qty > 0));
  };

  const total = cart.reduce((s, i) => s + (i.price * i.qty), 0);

  const handleCheckout = async () => {
    if (cart.length === 0) return;
    setLoading(true); setError('');
    try {
      await ordersAPI.create({
        vendor_id: vendorId,
        items: cart.map(i => ({ product_id: i.id, quantity: i.qty, price: i.price, name: i.name })),
        delivery_type: deliveryType,
      });
      navigation.navigate('Orders');
    } catch (e) { setError(e.response?.data?.error || 'Order failed'); }
    finally { setLoading(false); }
  };

  return (
    <ScrollView style={styles.container}>
      <GradientHeader title="Your Cart" subtitle={vendorName} />
      <View style={styles.content}>
        {error ? <Text style={styles.error}>{error}</Text> : null}

        {cart.map((item) => (
          <View key={item.id} style={styles.item}>
            <View style={styles.itemInfo}>
              <Text style={styles.itemName}>{item.name}</Text>
              <Text style={styles.itemPrice}>${(item.price * item.qty).toFixed(2)}</Text>
            </View>
            <View style={styles.qtyRow}>
              <TouchableOpacity onPress={() => updateQty(item.id, -1)} style={styles.qtyBtn}>
                <Feather name="minus" size={16} color={COLORS.dark} />
              </TouchableOpacity>
              <Text style={styles.qtyText}>{item.qty}</Text>
              <TouchableOpacity onPress={() => updateQty(item.id, 1)} style={styles.qtyBtn}>
                <Feather name="plus" size={16} color={COLORS.dark} />
              </TouchableOpacity>
            </View>
          </View>
        ))}

        <Text style={styles.label}>Delivery Type</Text>
        <View style={styles.deliveryRow}>
          {['pickup', 'delivery'].map((type) => (
            <TouchableOpacity key={type} style={[styles.deliveryChip, deliveryType === type && styles.deliveryActive]}
              onPress={() => setDeliveryType(type)}>
              <Feather name={type === 'pickup' ? 'shopping-bag' : 'truck'} size={18}
                color={deliveryType === type ? COLORS.white : COLORS.dark} />
              <Text style={[styles.deliveryText, deliveryType === type && styles.deliveryTextActive]}>
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.totalRow}>
          <Text style={styles.totalLabel}>Total</Text>
          <Text style={styles.totalAmount}>${total.toFixed(2)}</Text>
        </View>

        <Button title={`Place Order - $${total.toFixed(2)}`} onPress={handleCheckout} loading={loading} style={{ marginTop: 20 }} />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: SPACING.lg },
  error: { backgroundColor: '#fde8e8', color: COLORS.danger, padding: 12, borderRadius: RADIUS.sm, textAlign: 'center', marginBottom: 12 },
  item: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: 14, marginBottom: 8, ...SHADOWS.small },
  itemInfo: { flex: 1 },
  itemName: { fontSize: 15, fontWeight: '500', color: COLORS.dark },
  itemPrice: { fontSize: 14, color: COLORS.primary, marginTop: 2 },
  qtyRow: { flexDirection: 'row', alignItems: 'center' },
  qtyBtn: { width: 32, height: 32, borderRadius: 16, backgroundColor: COLORS.lightGrey, alignItems: 'center', justifyContent: 'center' },
  qtyText: { fontSize: 16, fontWeight: '600', marginHorizontal: 12, color: COLORS.dark },
  label: { fontSize: 16, fontWeight: '600', color: COLORS.dark, marginTop: 20, marginBottom: 10 },
  deliveryRow: { flexDirection: 'row', gap: 12 },
  deliveryChip: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', padding: 14, borderRadius: RADIUS.md, backgroundColor: COLORS.white, borderWidth: 1, borderColor: COLORS.border, gap: 8 },
  deliveryActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  deliveryText: { fontSize: 14, color: COLORS.dark },
  deliveryTextActive: { color: COLORS.white, fontWeight: '600' },
  totalRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 24, paddingVertical: 16, borderTopWidth: 1, borderTopColor: COLORS.border },
  totalLabel: { fontSize: 18, fontWeight: '600', color: COLORS.dark },
  totalAmount: { fontSize: 24, fontWeight: '700', color: COLORS.primary },
});
