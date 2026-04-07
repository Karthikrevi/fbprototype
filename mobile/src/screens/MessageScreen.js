import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, FlatList, TextInput, TouchableOpacity, KeyboardAvoidingView, Platform } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS, SPACING, RADIUS } from '../constants/theme';
import { chatAPI } from '../services/api';
import LoadingScreen from '../components/LoadingScreen';

export default function MessageScreen({ route }) {
  const { conversationId, vendorName } = route.params;
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const flatRef = useRef(null);

  const load = async () => {
    try { const res = await chatAPI.messages(conversationId); setMessages(res.data.messages || []); }
    catch {} finally { setLoading(false); }
  };

  useEffect(() => { load(); const interval = setInterval(load, 5000); return () => clearInterval(interval); }, [conversationId]);

  const handleSend = async () => {
    if (!text.trim()) return;
    setSending(true);
    try {
      await chatAPI.send(conversationId, text.trim());
      setText('');
      await load();
    } catch {} finally { setSending(false); }
  };

  if (loading) return <LoadingScreen />;

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined} keyboardVerticalOffset={90}>
      <FlatList ref={flatRef} data={messages} keyExtractor={(_, i) => String(i)}
        contentContainerStyle={styles.list}
        onContentSizeChange={() => flatRef.current?.scrollToEnd()}
        renderItem={({ item }) => (
          <View style={[styles.bubble, item.is_mine ? styles.myBubble : styles.theirBubble]}>
            <Text style={[styles.msgText, item.is_mine && styles.myText]}>{item.message}</Text>
            <Text style={[styles.time, item.is_mine && styles.myTime]}>{item.timestamp?.split(' ')[1] || ''}</Text>
          </View>
        )}
      />
      <View style={styles.inputBar}>
        <TextInput style={styles.input} placeholder="Type a message..." placeholderTextColor={COLORS.grey}
          value={text} onChangeText={setText} multiline returnKeyType="send" onSubmitEditing={handleSend} />
        <TouchableOpacity style={styles.sendBtn} onPress={handleSend} disabled={sending || !text.trim()}>
          <Feather name="send" size={20} color={COLORS.white} />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  list: { padding: SPACING.md, paddingBottom: 8 },
  bubble: { maxWidth: '80%', borderRadius: RADIUS.md, padding: 12, marginBottom: 8 },
  myBubble: { backgroundColor: COLORS.primary, alignSelf: 'flex-end', borderBottomRightRadius: 4 },
  theirBubble: { backgroundColor: COLORS.white, alignSelf: 'flex-start', borderBottomLeftRadius: 4 },
  msgText: { fontSize: 15, color: COLORS.dark },
  myText: { color: COLORS.white },
  time: { fontSize: 10, color: COLORS.grey, marginTop: 4 },
  myTime: { color: 'rgba(255,255,255,0.7)' },
  inputBar: { flexDirection: 'row', alignItems: 'flex-end', padding: SPACING.sm, backgroundColor: COLORS.white, borderTopWidth: 1, borderTopColor: COLORS.lightGrey },
  input: { flex: 1, backgroundColor: COLORS.light, borderRadius: RADIUS.md, paddingHorizontal: 14, paddingVertical: 10, fontSize: 15, color: COLORS.dark, maxHeight: 100 },
  sendBtn: { width: 42, height: 42, borderRadius: 21, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center', marginLeft: 8 },
});
