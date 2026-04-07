import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, RefreshControl } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { chatAPI } from '../services/api';
import EmptyState from '../components/EmptyState';
import GradientHeader from '../components/GradientHeader';

export default function ConversationsScreen({ navigation }) {
  const [conversations, setConversations] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try { const res = await chatAPI.conversations(); setConversations(res.data.conversations || []); } catch {}
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));
  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  return (
    <View style={styles.container}>
      <GradientHeader title="Messages" subtitle={`${conversations.length} conversation${conversations.length !== 1 ? 's' : ''}`} />
      <FlatList data={conversations} keyExtractor={(c) => String(c.id)}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListEmptyComponent={<EmptyState icon="message-circle" title="No messages" message="Start a conversation with a vendor" />}
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.card} onPress={() => navigation.navigate('Message', { conversationId: item.id, vendorName: item.vendor_name })}>
            <View style={styles.avatar}>
              <Feather name="message-circle" size={22} color={COLORS.primary} />
            </View>
            <View style={styles.cardBody}>
              <Text style={styles.name}>{item.vendor_name}</Text>
              <Text style={styles.lastMsg} numberOfLines={1}>{item.last_message || 'Start chatting...'}</Text>
            </View>
            {item.unread_count > 0 && (
              <View style={styles.unread}><Text style={styles.unreadText}>{item.unread_count}</Text></View>
            )}
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  list: { padding: SPACING.md },
  card: { flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: 14, marginBottom: 8, ...SHADOWS.small },
  avatar: { width: 44, height: 44, borderRadius: 22, backgroundColor: COLORS.primary + '15', alignItems: 'center', justifyContent: 'center' },
  cardBody: { flex: 1, marginLeft: 12 },
  name: { fontSize: 15, fontWeight: '600', color: COLORS.dark },
  lastMsg: { fontSize: 13, color: COLORS.grey, marginTop: 2 },
  unread: { backgroundColor: COLORS.primary, borderRadius: 12, paddingHorizontal: 8, paddingVertical: 2, minWidth: 24, alignItems: 'center' },
  unreadText: { fontSize: 12, fontWeight: '700', color: COLORS.white },
});
