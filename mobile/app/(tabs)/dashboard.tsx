import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { useRouter } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '@/contexts/AuthContext';
import { fetchDashboardStats, DashboardStats } from '@/services/profile';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { COLORS, SPACING, BORDER_RADIUS } from '@/config/constants';
import { formatDistanceToNow } from 'date-fns';

const getStatusVariant = (
  status: string
): 'success' | 'info' | 'secondary' | 'warning' | 'danger' => {
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

export default function DashboardScreen() {
  const { user } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await fetchDashboardStats();
      setStats(data);
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

  if (isLoading) return <LoadingSpinner />;

  const statsCards = [
    {
      title: 'Total Campaigns',
      value: stats?.total_campaigns ?? 0,
      icon: 'send' as const,
      color: COLORS.primaryLight,
    },
    {
      title: 'Total Contacts',
      value: stats?.total_contacts?.toLocaleString() ?? '0',
      icon: 'people' as const,
      color: COLORS.info,
    },
    {
      title: 'Emails Sent',
      value: stats?.emails_sent?.toLocaleString() ?? '0',
      icon: 'mail' as const,
      color: COLORS.success,
    },
    {
      title: 'Open Rate',
      value: `${stats?.open_rate ?? 0}%`,
      icon: 'bar-chart' as const,
      color: COLORS.warning,
    },
  ];

  return (
    <View style={styles.container}>
      <StatusBar style="light" />

      {/* Header */}
      <LinearGradient
        colors={['#1e293b', '#0f172a']}
        style={styles.header}
      >
        <View>
          <Text style={styles.greeting}>
            Hello, {user?.first_name || 'there'} 👋
          </Text>
          <Text style={styles.orgName}>{user?.organization?.name}</Text>
        </View>
        <TouchableOpacity
          style={styles.profileBtn}
          onPress={() => router.push('/(tabs)/profile')}
        >
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {user?.first_name?.[0]?.toUpperCase() || 'U'}
            </Text>
          </View>
        </TouchableOpacity>
      </LinearGradient>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={COLORS.primaryLight}
          />
        }
      >
        {/* Stats Grid */}
        <Text style={styles.sectionTitle}>Overview</Text>
        <View style={styles.statsGrid}>
          {statsCards.map((card) => (
            <Card key={card.title} style={styles.statCard}>
              <View
                style={[
                  styles.statIcon,
                  { backgroundColor: card.color + '20' },
                ]}
              >
                <Ionicons name={card.icon} size={20} color={card.color} />
              </View>
              <Text style={styles.statValue}>{card.value}</Text>
              <Text style={styles.statTitle}>{card.title}</Text>
            </Card>
          ))}
        </View>

        {/* Recent Campaigns */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Recent Campaigns</Text>
          <TouchableOpacity onPress={() => router.push('/(tabs)/campaigns')}>
            <Text style={styles.viewAll}>View all</Text>
          </TouchableOpacity>
        </View>

        {stats?.recent_campaigns && stats.recent_campaigns.length > 0 ? (
          stats.recent_campaigns.slice(0, 5).map((campaign) => (
            <Card key={campaign.id} style={styles.campaignItem}>
              <View style={styles.campaignRow}>
                <View style={styles.campaignInfo}>
                  <Text style={styles.campaignName} numberOfLines={1}>
                    {campaign.name}
                  </Text>
                  <Text style={styles.campaignDate}>
                    {formatDistanceToNow(new Date(campaign.created_at), {
                      addSuffix: true,
                    })}
                  </Text>
                </View>
                <Badge
                  label={campaign.status}
                  variant={getStatusVariant(campaign.status)}
                />
              </View>
            </Card>
          ))
        ) : (
          <Card style={styles.emptyCard}>
            <View style={styles.emptyCardContent}>
              <Ionicons name="send-outline" size={32} color={COLORS.textMuted} />
              <Text style={styles.emptyText}>No campaigns yet</Text>
              <TouchableOpacity
                style={styles.createBtn}
                onPress={() => router.push('/(tabs)/campaigns')}
              >
                <Text style={styles.createBtnText}>Create Campaign</Text>
              </TouchableOpacity>
            </View>
          </Card>
        )}

        {/* Recent Activity */}
        {stats?.recent_activity && stats.recent_activity.length > 0 && (
          <>
            <Text style={[styles.sectionTitle, { marginTop: SPACING.lg }]}>
              Recent Activity
            </Text>
            {stats.recent_activity.slice(0, 5).map((activity) => (
              <Card key={activity.id} style={styles.activityItem}>
                <View style={styles.activityRow}>
                  <View
                    style={[
                      styles.activityIcon,
                      {
                        backgroundColor:
                          activity.status === 'delivered'
                            ? '#166534'
                            : activity.status === 'opened'
                            ? '#1e3a5f'
                            : '#334155',
                      },
                    ]}
                  >
                    <Ionicons
                      name={
                        activity.status === 'delivered'
                          ? 'checkmark-circle'
                          : activity.status === 'opened'
                          ? 'mail-open'
                          : 'mail'
                      }
                      size={14}
                      color={
                        activity.status === 'delivered'
                          ? COLORS.success
                          : activity.status === 'opened'
                          ? COLORS.info
                          : COLORS.textMuted
                      }
                    />
                  </View>
                  <View style={styles.activityContent}>
                    <Text style={styles.activityRecipient} numberOfLines={1}>
                      {activity.recipient}
                    </Text>
                    <Text style={styles.activityMeta} numberOfLines={1}>
                      {activity.campaign_name} •{' '}
                      {activity.status.charAt(0).toUpperCase() +
                        activity.status.slice(1)}
                    </Text>
                  </View>
                </View>
              </Card>
            ))}
          </>
        )}
      </ScrollView>
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
    paddingBottom: SPACING.lg,
  },
  greeting: { color: COLORS.text, fontSize: 22, fontWeight: '700' },
  orgName: { color: COLORS.textMuted, fontSize: 13, marginTop: 2 },
  profileBtn: {},
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { color: COLORS.white, fontSize: 16, fontWeight: '700' },
  scroll: { flex: 1 },
  scrollContent: { padding: SPACING.lg, paddingBottom: SPACING.xxl },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.sm,
    marginTop: SPACING.lg,
  },
  sectionTitle: {
    color: COLORS.text,
    fontSize: 16,
    fontWeight: '700',
    marginBottom: SPACING.sm,
  },
  viewAll: { color: COLORS.primaryLight, fontSize: 13, fontWeight: '600' },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
    marginBottom: SPACING.md,
  },
  statCard: {
    width: '47.5%',
    padding: SPACING.md,
    gap: 6,
  },
  statIcon: {
    width: 40,
    height: 40,
    borderRadius: BORDER_RADIUS.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  statValue: { color: COLORS.text, fontSize: 22, fontWeight: '700' },
  statTitle: { color: COLORS.textMuted, fontSize: 12 },
  campaignItem: { marginBottom: SPACING.sm },
  campaignRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  campaignInfo: { flex: 1, marginRight: SPACING.sm },
  campaignName: { color: COLORS.text, fontSize: 14, fontWeight: '600' },
  campaignDate: { color: COLORS.textMuted, fontSize: 12, marginTop: 2 },
  emptyCard: { alignItems: 'center', padding: SPACING.xl },
  emptyCardContent: { alignItems: 'center', gap: SPACING.sm },
  emptyText: { color: COLORS.textMuted, fontSize: 14 },
  createBtn: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderRadius: BORDER_RADIUS.md,
    marginTop: SPACING.sm,
  },
  createBtnText: { color: COLORS.white, fontSize: 13, fontWeight: '600' },
  activityItem: { marginBottom: SPACING.sm },
  activityRow: { flexDirection: 'row', alignItems: 'center', gap: SPACING.sm },
  activityIcon: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  activityContent: { flex: 1 },
  activityRecipient: {
    color: COLORS.text,
    fontSize: 13,
    fontWeight: '600',
  },
  activityMeta: { color: COLORS.textMuted, fontSize: 12, marginTop: 2 },
});
