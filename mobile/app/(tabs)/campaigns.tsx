import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  Alert,
  TextInput,
} from 'react-native';
import { useRouter } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import {
  fetchCampaigns,
  Campaign,
  sendCampaign,
  pauseCampaign,
  resumeCampaign,
  deleteCampaign,
} from '@/services/campaigns';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { COLORS, SPACING, BORDER_RADIUS } from '@/config/constants';
import { formatDistanceToNow } from 'date-fns';

type BadgeVariant = 'success' | 'info' | 'secondary' | 'warning' | 'danger';

const getStatusVariant = (status: string): BadgeVariant => {
  switch (status?.toUpperCase()) {
    case 'SENT': return 'success';
    case 'SENDING': return 'info';
    case 'DRAFT': return 'secondary';
    case 'SCHEDULED': return 'warning';
    case 'PAUSED': return 'warning';
    case 'CANCELLED': return 'danger';
    default: return 'secondary';
  }
};

export default function CampaignsScreen() {
  const router = useRouter();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');

  const load = useCallback(async () => {
    try {
      const data = await fetchCampaigns();
      setCampaigns(data);
    } catch {
      // silently fail
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const onRefresh = () => {
    setRefreshing(true);
    load();
  };

  const handleAction = async (campaign: Campaign) => {
    const status = campaign.status?.toUpperCase();
    if (status === 'DRAFT' || status === 'SCHEDULED') {
      Alert.alert('Send Campaign', `Send "${campaign.name}" now?`, [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Send',
          onPress: async () => {
            try {
              const updated = await sendCampaign(campaign.id);
              setCampaigns((prev) =>
                prev.map((c) => (c.id === campaign.id ? { ...c, ...updated } : c))
              );
            } catch {
              Alert.alert('Error', 'Failed to send campaign');
            }
          },
        },
      ]);
    } else if (status === 'SENDING') {
      Alert.alert('Pause Campaign', `Pause "${campaign.name}"?`, [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Pause',
          onPress: async () => {
            try {
              const updated = await pauseCampaign(campaign.id);
              setCampaigns((prev) =>
                prev.map((c) => (c.id === campaign.id ? { ...c, ...updated } : c))
              );
            } catch {
              Alert.alert('Error', 'Failed to pause campaign');
            }
          },
        },
      ]);
    } else if (status === 'PAUSED') {
      Alert.alert('Resume Campaign', `Resume "${campaign.name}"?`, [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Resume',
          onPress: async () => {
            try {
              const updated = await resumeCampaign(campaign.id);
              setCampaigns((prev) =>
                prev.map((c) => (c.id === campaign.id ? { ...c, ...updated } : c))
              );
            } catch {
              Alert.alert('Error', 'Failed to resume campaign');
            }
          },
        },
      ]);
    }
  };

  const handleDelete = (campaign: Campaign) => {
    Alert.alert(
      'Delete Campaign',
      `Are you sure you want to delete "${campaign.name}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await deleteCampaign(campaign.id);
              setCampaigns((prev) => prev.filter((c) => c.id !== campaign.id));
            } catch {
              Alert.alert('Error', 'Failed to delete campaign');
            }
          },
        },
      ]
    );
  };

  const filtered = campaigns.filter(
    (c) =>
      c.name?.toLowerCase().includes(search.toLowerCase()) ||
      c.subject?.toLowerCase().includes(search.toLowerCase())
  );

  const getActionIcon = (status: string) => {
    const s = status?.toUpperCase();
    if (s === 'SENDING') return 'pause-circle-outline';
    if (s === 'PAUSED') return 'play-circle-outline';
    if (s === 'DRAFT' || s === 'SCHEDULED') return 'send-outline';
    return null;
  };

  const renderItem = ({ item }: { item: Campaign }) => {
    const actionIcon = getActionIcon(item.status);
    return (
      <Card style={styles.card}>
        <TouchableOpacity
          activeOpacity={0.8}
          onPress={() => router.push(`/(tabs)/campaign/${item.id}` as any)}
        >
          <View style={styles.cardHeader}>
            <View style={styles.cardInfo}>
              <Text style={styles.cardTitle} numberOfLines={1}>
                {item.name}
              </Text>
              <Text style={styles.cardSubtitle} numberOfLines={1}>
                {item.subject || 'No subject'}
              </Text>
            </View>
            <Badge label={item.status} variant={getStatusVariant(item.status)} />
          </View>

          {/* Stats Row */}
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Ionicons name="mail-outline" size={14} color={COLORS.textMuted} />
              <Text style={styles.statText}>{item.stats_sent ?? 0} sent</Text>
            </View>
            <View style={styles.statItem}>
              <Ionicons name="mail-open-outline" size={14} color={COLORS.info} />
              <Text style={styles.statText}>{item.stats_opened ?? 0} opened</Text>
            </View>
            <View style={styles.statItem}>
              <Ionicons name="hand-left-outline" size={14} color={COLORS.success} />
              <Text style={styles.statText}>{item.stats_clicked ?? 0} clicked</Text>
            </View>
          </View>

          <Text style={styles.cardDate}>
            {formatDistanceToNow(new Date(item.updated_at || item.created_at), {
              addSuffix: true,
            })}
          </Text>
        </TouchableOpacity>

        {/* Actions */}
        <View style={styles.actions}>
          {actionIcon && (
            <TouchableOpacity
              style={styles.actionBtn}
              onPress={() => handleAction(item)}
            >
              <Ionicons name={actionIcon as any} size={20} color={COLORS.primaryLight} />
            </TouchableOpacity>
          )}
          <TouchableOpacity
            style={styles.actionBtn}
            onPress={() => handleDelete(item)}
          >
            <Ionicons name="trash-outline" size={20} color={COLORS.error} />
          </TouchableOpacity>
        </View>
      </Card>
    );
  };

  if (isLoading) return <LoadingSpinner />;

  return (
    <View style={styles.container}>
      <StatusBar style="light" />

      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Campaigns</Text>
          <Text style={styles.subtitle}>Manage your email campaigns</Text>
        </View>
      </View>

      {/* Search */}
      <View style={styles.searchContainer}>
        <View style={styles.searchWrapper}>
          <Ionicons name="search-outline" size={18} color={COLORS.textMuted} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search campaigns..."
            placeholderTextColor={COLORS.textMuted}
            value={search}
            onChangeText={setSearch}
          />
          {search ? (
            <TouchableOpacity onPress={() => setSearch('')}>
              <Ionicons name="close-circle" size={18} color={COLORS.textMuted} />
            </TouchableOpacity>
          ) : null}
        </View>
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
            icon="send-outline"
            title="No campaigns found"
            description={
              search
                ? 'No campaigns match your search'
                : 'Create your first campaign to get started'
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
    paddingHorizontal: SPACING.lg,
    paddingTop: 56,
    paddingBottom: SPACING.md,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  title: { color: COLORS.text, fontSize: 24, fontWeight: '700' },
  subtitle: { color: COLORS.textMuted, fontSize: 13, marginTop: 2 },
  searchContainer: {
    padding: SPACING.md,
    backgroundColor: COLORS.surface,
  },
  searchWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surfaceLight,
    borderRadius: BORDER_RADIUS.md,
    paddingHorizontal: SPACING.md,
    gap: SPACING.sm,
  },
  searchInput: {
    flex: 1,
    color: COLORS.text,
    fontSize: 14,
    paddingVertical: 10,
  },
  list: { padding: SPACING.md, gap: SPACING.sm, paddingBottom: SPACING.xxl },
  card: { marginBottom: 0 },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: SPACING.sm,
  },
  cardInfo: { flex: 1, marginRight: SPACING.sm },
  cardTitle: { color: COLORS.text, fontSize: 15, fontWeight: '600' },
  cardSubtitle: { color: COLORS.textMuted, fontSize: 13, marginTop: 2 },
  statsRow: {
    flexDirection: 'row',
    gap: SPACING.md,
    marginBottom: SPACING.sm,
  },
  statItem: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  statText: { color: COLORS.textMuted, fontSize: 12 },
  cardDate: { color: COLORS.textMuted, fontSize: 11 },
  actions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    paddingTop: SPACING.sm,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    marginTop: SPACING.sm,
    gap: SPACING.sm,
  },
  actionBtn: {
    padding: 6,
    backgroundColor: COLORS.surfaceLight,
    borderRadius: BORDER_RADIUS.sm,
  },
});
