import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, FlatList, RefreshControl } from 'react-native';
import { COLORS, SPACING, RADIUS, SHADOWS } from '../constants/theme';
import { communityAPI } from '../services/api';
import Card from '../components/Card';
import EmptyState from '../components/EmptyState';
import GradientHeader from '../components/GradientHeader';
import LoadingScreen from '../components/LoadingScreen';

export default function CommunityScreen() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = async () => {
    try { const res = await communityAPI.posts(); setPosts(res.data.posts || []); }
    catch {} finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);
  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  if (loading) return <LoadingScreen />;

  return (
    <View style={styles.container}>
      <GradientHeader title="Community Posts" subtitle="Connect with other pet parents" />
      <FlatList data={posts} keyExtractor={(_, i) => String(i)}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListEmptyComponent={<EmptyState icon="users" title="No posts yet" message="Community posts will appear here" />}
        renderItem={({ item }) => (
          <Card>
            <Text style={styles.postTitle}>{item.title || 'Community Post'}</Text>
            <Text style={styles.postContent}>{item.content}</Text>
            <Text style={styles.postMeta}>By {item.author || 'Anonymous'} • {item.created_at || ''}</Text>
          </Card>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  list: { padding: SPACING.md },
  postTitle: { fontSize: 16, fontWeight: '600', color: COLORS.dark },
  postContent: { fontSize: 14, color: COLORS.dark, marginTop: 6, lineHeight: 20 },
  postMeta: { fontSize: 12, color: COLORS.grey, marginTop: 8 },
});
