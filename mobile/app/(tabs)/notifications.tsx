import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Alert,
  RefreshControl,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import { useNotifications } from '@/hooks/useNotifications';
import { deleteNotification } from '@/services/notifications';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { COLORS, SPACING, BORDER_RADIUS } from '@/config/constants';
import { formatDistanceToNow } from 'date-fns';
import type { Notification } from '@/services/notifications';

const getNotifIcon = (type: string): { icon: string; color: string; bg: string } => {
  switch (type) {
    case 'CAMPAIGN_SENT':
      return { icon: 'mail', color: COLORS.info, bg: '#1e3a5f' };
    case 'CONTACT_ADDED':
      return { icon: 'person-add', color: COLORS.success, bg: '#166534' };
    default:
      return { icon: 'alert-circle', color: COLORS.warning, bg: '#92400e' };
  }
};

export default function NotificationsScreen() {
  const { notifications, unreadCount, markAsRead, markAllAsRead, refresh, loading } =
    useNotifications();
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'all' | 'unread' | 'read'>('all');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const onRefresh = async () => {
    setRefreshing(true);
    await refresh();
    setRefreshing(false);
  };

  const handleMarkRead = async (n: Notification) => {
    if (!n.is_read) {
      await markAsRead(n.id);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllAsRead();
    } catch {
      Alert.alert('Error', 'Failed to mark all as read');
    }
  };

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    try {
      await deleteNotification(id);
      await refresh();
    } catch {
      Alert.alert('Error', 'Failed to delete notification');
    } finally {
      setDeletingId(null);
    }
  };

  const filtered = notifications.filter((n) => {
    if (activeTab === 'unread') return !n.is_read;
    if (activeTab === 'read') return n.is_read;
    return true;
  });

  const renderItem = ({ item }: { item: Notification }) => {
    const { icon, color, bg } = getNotifIcon(item.notification_type);
    return (
      <TouchableOpacity
        activeOpacity={0.8}
        onPress={() => handleMarkRead(item)}
      >
        <Card
          style={[
            styles.notifCard,
            !item.is_read && styles.unreadCard,
          ]}
        >
          <View style={styles.notifRow}>
            <View style={[styles.notifIcon, { backgroundColor: bg }]}>
              <Ionicons name={icon as any} size={18} color={color} />
            </View>
            <View style={styles.notifContent}>
              <View style={styles.notifHeader}>
                <Text style={styles.notifTitle} numberOfLines={1}>
                  {item.title}
                </Text>
                {!item.is_read && <View style={styles.unreadDot} />}
              </View>
              <Text style={styles.notifMessage} numberOfLines={2}>
                {item.message}
              </Text>
              <Text style={styles.notifTime}>
                {formatDistanceToNow(new Date(item.created_at), {
                  addSuffix: true,
                })}
              </Text>
            </View>
            <TouchableOpacity
              style={styles.deleteBtn}
              onPress={() => handleDelete(item.id)}
              disabled={deletingId === item.id}
            >
              <Ionicons name="trash-outline" size={16} color={COLORS.error} />
            </TouchableOpacity>
          </View>
        </Card>
      </TouchableOpacity>
    );
  };

  if (loading) return <LoadingSpinner />;

  return (
    <View style={styles.container}>
      <StatusBar style="light" />

      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Notifications</Text>
          {unreadCount > 0 && (
            <Text style={styles.subtitle}>{unreadCount} unread</Text>
          )}
        </View>
        {unreadCount > 0 && (
          <TouchableOpacity style={styles.markAllBtn} onPress={handleMarkAllRead}>
            <Ionicons name="checkmark-done-outline" size={18} color={COLORS.primaryLight} />
            <Text style={styles.markAllText}>Mark all read</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        {(['all', 'unread', 'read'] as const).map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.tabActive]}
            onPress={() => setActiveTab(tab)}
          >
            <Text
              style={[styles.tabText, activeTab === tab && styles.tabTextActive]}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList
        data={filtered}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={COLORS.primaryLight}
          />
        }
        ListEmptyComponent={
          <EmptyState
            icon="notifications-off-outline"
            title="No notifications"
            description={
              activeTab === 'unread'
                ? "You're all caught up!"
                : 'No notifications to show'
            }
          />
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: SPACING.lg,
    paddingTop: 56,
    paddingBottom: SPACING.md,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  title: { color: COLORS.text, fontSize: 24, fontWeight: '700' },
  subtitle: { color: COLORS.primaryLight, fontSize: 13, marginTop: 2 },
  markAllBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: COLORS.surfaceLight,
    paddingHorizontal: SPACING.sm,
    paddingVertical: 6,
    borderRadius: BORDER_RADIUS.md,
  },
  markAllText: { color: COLORS.primaryLight, fontSize: 12, fontWeight: '500' },
  tabs: {
    flexDirection: 'row',
    backgroundColor: COLORS.surface,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    gap: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  tab: {
    paddingHorizontal: SPACING.md,
    paddingVertical: 6,
    borderRadius: BORDER_RADIUS.full,
    backgroundColor: COLORS.surfaceLight,
  },
  tabActive: { backgroundColor: COLORS.primary },
  tabText: { color: COLORS.textMuted, fontSize: 13, fontWeight: '500' },
  tabTextActive: { color: COLORS.white },
  list: { padding: SPACING.md, gap: SPACING.sm, paddingBottom: SPACING.xxl },
  notifCard: { borderLeftWidth: 3, borderLeftColor: 'transparent' },
  unreadCard: { borderLeftColor: COLORS.primaryLight },
  notifRow: { flexDirection: 'row', alignItems: 'flex-start', gap: SPACING.sm },
  notifIcon: {
    width: 36,
    height: 36,
    borderRadius: BORDER_RADIUS.md,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  notifContent: { flex: 1 },
  notifHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    marginBottom: 4,
  },
  notifTitle: {
    color: COLORS.text,
    fontSize: 14,
    fontWeight: '600',
    flex: 1,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: COLORS.primaryLight,
  },
  notifMessage: { color: COLORS.textMuted, fontSize: 13, lineHeight: 18 },
  notifTime: { color: COLORS.textMuted, fontSize: 11, marginTop: 4 },
  deleteBtn: { padding: 4 },
});
