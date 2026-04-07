import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, Image, ScrollView } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { marketplaceAPI } from '../services/api';
import Button from '../components/Button';
import Badge from '../components/Badge';
import LoadingScreen from '../components/LoadingScreen';

export default function VendorShopScreen({ route, navigation }) {
  const { vendorId } = route.params;
  const [vendor, setVendor] = useState(null);
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCat, setSelectedCat] = useState('All');
  const [cart, setCart] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await marketplaceAPI.vendor(vendorId);
        setVendor(res.data.vendor);
        setProducts(res.data.products || []);
        const cats = ['All', ...new Set((res.data.products || []).map(p => p.category).filter(Boolean))];
        setCategories(cats);
      } catch {} finally { setLoading(false); }
    })();
  }, [vendorId]);

  const addToCart = (product) => {
    setCart(prev => {
      const existing = prev.find(i => i.id === product.id);
      if (existing) return prev.map(i => i.id === product.id ? { ...i, qty: i.qty + 1 } : i);
      return [...prev, { ...product, qty: 1 }];
    });
  };

  const filtered = selectedCat === 'All' ? products : products.filter(p => p.category === selectedCat);
  const cartTotal = cart.reduce((sum, i) => sum + (i.price * i.qty), 0);

  if (loading) return <LoadingScreen />;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>{vendor?.name || 'Shop'}</Text>
        <Text style={styles.subtitle}>{vendor?.city}</Text>
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.catScroll}>
        {categories.map((c) => (
          <TouchableOpacity key={c} style={[styles.catChip, selectedCat === c && styles.catChipActive]}
            onPress={() => setSelectedCat(c)}>
            <Text style={[styles.catText, selectedCat === c && styles.catTextActive]}>{c}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <FlatList data={filtered} keyExtractor={(p) => String(p.id)} contentContainerStyle={styles.list}
        renderItem={({ item }) => (
          <View style={styles.productCard}>
            <View style={styles.productInfo}>
              <Text style={styles.productName}>{item.name}</Text>
              <Text style={styles.productCat}>{item.category}</Text>
              <View style={styles.priceRow}>
                <Text style={styles.price}>${item.price}</Text>
                {item.discount > 0 && <Badge text={`${item.discount}% OFF`} color={COLORS.danger} />}
              </View>
            </View>
            <TouchableOpacity style={styles.addBtn} onPress={() => addToCart(item)}>
              <Feather name="plus" size={18} color={COLORS.white} />
            </TouchableOpacity>
          </View>
        )}
      />

      {cart.length > 0 && (
        <TouchableOpacity style={styles.cartBar} onPress={() => navigation.navigate('Cart', { cart, vendorId, vendorName: vendor?.name })}>
          <Text style={styles.cartText}>{cart.reduce((s, i) => s + i.qty, 0)} items • ${cartTotal.toFixed(2)}</Text>
          <Text style={styles.cartAction}>View Cart →</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: { backgroundColor: COLORS.primary, paddingTop: 50, paddingBottom: 16, paddingHorizontal: SPACING.lg },
  title: { fontSize: 22, fontWeight: '700', color: COLORS.white },
  subtitle: { fontSize: 13, color: 'rgba(255,255,255,0.8)', marginTop: 4 },
  catScroll: { paddingHorizontal: SPACING.md, paddingVertical: SPACING.sm },
  catChip: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: RADIUS.full, backgroundColor: COLORS.white, marginRight: 8, borderWidth: 1, borderColor: COLORS.border },
  catChipActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  catText: { fontSize: 13, color: COLORS.dark },
  catTextActive: { color: COLORS.white, fontWeight: '600' },
  list: { padding: SPACING.md },
  productCard: { flexDirection: 'row', backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: 14, marginBottom: 10, ...SHADOWS.small, alignItems: 'center' },
  productInfo: { flex: 1 },
  productName: { fontSize: 15, fontWeight: '600', color: COLORS.dark },
  productCat: { fontSize: 12, color: COLORS.grey, marginTop: 2 },
  priceRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 6 },
  price: { fontSize: 17, fontWeight: '700', color: COLORS.primary },
  addBtn: { width: 36, height: 36, borderRadius: 18, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  cartBar: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: COLORS.primary, paddingHorizontal: 20, paddingVertical: 16, margin: SPACING.md, borderRadius: RADIUS.md },
  cartText: { color: COLORS.white, fontSize: 15, fontWeight: '600' },
  cartAction: { color: COLORS.white, fontSize: 14, fontWeight: '500' },
});
