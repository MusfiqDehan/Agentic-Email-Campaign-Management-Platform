import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import {
  fetchCampaignById,
  Campaign,
  sendCampaign,
  pauseCampaign,
  resumeCampaign,
} from '@/services/campaigns';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { COLORS, SPACING, BORDER_RADIUS } from '@/config/constants';

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

export default function CampaignDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (id) {
      fetchCampaignById(id)
        .then(setCampaign)
        .catch(() => Alert.alert('Error', 'Failed to load campaign'))
        .finally(() => setIsLoading(false));
    }
  }, [id]);

  const handleSend = async () => {
    if (!campaign) return;
    Alert.alert('Send Campaign', `Send "${campaign.name}" now?`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Send',
        onPress: async () => {
          setActionLoading(true);
          try {
            const updated = await sendCampaign(campaign.id);
            setCampaign({ ...campaign, ...updated });
          } catch {
            Alert.alert('Error', 'Failed to send campaign');
          } finally {
            setActionLoading(false);
          }
        },
      },
    ]);
  };

  const handlePause = async () => {
    if (!campaign) return;
    setActionLoading(true);
    try {
      const updated = await pauseCampaign(campaign.id);
      setCampaign({ ...campaign, ...updated });
    } catch {
      Alert.alert('Error', 'Failed to pause campaign');
    } finally {
      setActionLoading(false);
    }
  };

  const handleResume = async () => {
    if (!campaign) return;
    setActionLoading(true);
    try {
      const updated = await resumeCampaign(campaign.id);
      setCampaign({ ...campaign, ...updated });
    } catch {
      Alert.alert('Error', 'Failed to resume campaign');
    } finally {
      setActionLoading(false);
    }
  };

  if (isLoading) return <LoadingSpinner />;
  if (!campaign) return null;

  const status = campaign.status?.toUpperCase();
  const total = campaign.stats_total_recipients || 1;

  const deliveredRate = Math.round((campaign.stats_delivered / total) * 100);
  const openedRate = Math.round((campaign.stats_opened / total) * 100);
  const clickedRate = Math.round((campaign.stats_clicked / total) * 100);

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle} numberOfLines={1}>
          Campaign Details
        </Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Campaign Info */}
        <Card style={styles.infoCad}>
          <View style={styles.infoHeader}>
            <View style={styles.infoText}>
              <Text style={styles.campaignName}>{campaign.name}</Text>
              <Text style={styles.campaignSubject}>{campaign.subject}</Text>
            </View>
            <Badge label={campaign.status} variant={getStatusVariant(campaign.status)} />
          </View>
          {campaign.preview_text && (
            <Text style={styles.previewText}>{campaign.preview_text}</Text>
          )}
        </Card>

        {/* Stats */}
        <Text style={styles.sectionTitle}>Performance</Text>
        <View style={styles.statsGrid}>
          {[
            {
              label: 'Recipients',
              value: campaign.stats_total_recipients ?? 0,
              icon: 'people-outline',
              color: COLORS.primaryLight,
              rate: null,
            },
            {
              label: 'Sent',
              value: campaign.stats_sent ?? 0,
              icon: 'send-outline',
              color: COLORS.info,
              rate: null,
            },
            {
              label: 'Delivered',
              value: campaign.stats_delivered ?? 0,
              icon: 'checkmark-circle-outline',
              color: COLORS.success,
              rate: deliveredRate,
            },
            {
              label: 'Opened',
              value: campaign.stats_opened ?? 0,
              icon: 'mail-open-outline',
              color: COLORS.warning,
              rate: openedRate,
            },
            {
              label: 'Clicked',
              value: campaign.stats_clicked ?? 0,
              icon: 'hand-left-outline',
              color: '#a855f7',
              rate: clickedRate,
            },
          ].map((stat) => (
            <Card key={stat.label} style={styles.statCard}>
              <View style={[styles.statIconWrapper, { backgroundColor: stat.color + '20' }]}>
                <Ionicons name={stat.icon as any} size={18} color={stat.color} />
              </View>
              <Text style={styles.statValue}>{stat.value.toLocaleString()}</Text>
              <Text style={styles.statLabel}>{stat.label}</Text>
              {stat.rate !== null && (
                <Text style={[styles.statRate, { color: stat.color }]}>{stat.rate}%</Text>
              )}
            </Card>
          ))}
        </View>

        {/* Actions */}
        {(status === 'DRAFT' || status === 'SCHEDULED') && (
          <Button
            title="Send Campaign"
            onPress={handleSend}
            loading={actionLoading}
            style={styles.actionBtn}
            leftIcon={<Ionicons name="send" size={16} color={COLORS.white} />}
          />
        )}
        {status === 'SENDING' && (
          <Button
            title="Pause Campaign"
            variant="outline"
            onPress={handlePause}
            loading={actionLoading}
            style={styles.actionBtn}
          />
        )}
        {status === 'PAUSED' && (
          <Button
            title="Resume Campaign"
            onPress={handleResume}
            loading={actionLoading}
            style={styles.actionBtn}
          />
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
    paddingHorizontal: SPACING.md,
    paddingTop: 56,
    paddingBottom: SPACING.md,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  backBtn: { padding: 4 },
  headerTitle: {
    color: COLORS.text,
    fontSize: 16,
    fontWeight: '600',
    flex: 1,
    textAlign: 'center',
  },
  scroll: { flex: 1 },
  scrollContent: { padding: SPACING.md, paddingBottom: SPACING.xxl },
  infoCad: { marginBottom: SPACING.md },
  infoHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
  },
  infoText: { flex: 1, marginRight: SPACING.sm },
  campaignName: { color: COLORS.text, fontSize: 18, fontWeight: '700' },
  campaignSubject: { color: COLORS.textMuted, fontSize: 14, marginTop: 4 },
  previewText: {
    color: COLORS.textSecondary,
    fontSize: 13,
    marginTop: SPACING.sm,
    lineHeight: 18,
  },
  sectionTitle: {
    color: COLORS.text,
    fontSize: 15,
    fontWeight: '700',
    marginBottom: SPACING.sm,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
    marginBottom: SPACING.lg,
  },
  statCard: {
    width: '47%',
    padding: SPACING.md,
    alignItems: 'center',
    gap: 4,
  },
  statIconWrapper: {
    width: 36,
    height: 36,
    borderRadius: BORDER_RADIUS.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  statValue: { color: COLORS.text, fontSize: 20, fontWeight: '700' },
  statLabel: { color: COLORS.textMuted, fontSize: 12 },
  statRate: { fontSize: 12, fontWeight: '600' },
  actionBtn: { marginTop: SPACING.sm },
});
