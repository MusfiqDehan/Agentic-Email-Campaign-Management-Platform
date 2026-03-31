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
import { fetchTemplateById, Template, duplicateTemplate } from '@/services/templates';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { COLORS, SPACING, BORDER_RADIUS } from '@/config/constants';
import { formatDistanceToNow } from 'date-fns';

export default function TemplateDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [template, setTemplate] = useState<Template | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [duplicating, setDuplicating] = useState(false);

  useEffect(() => {
    if (id) {
      fetchTemplateById(id)
        .then(setTemplate)
        .catch(() => Alert.alert('Error', 'Failed to load template'))
        .finally(() => setIsLoading(false));
    }
  }, [id]);

  const handleDuplicate = async () => {
    if (!template) return;
    setDuplicating(true);
    try {
      await duplicateTemplate(template.id);
      Alert.alert('Success', 'Template duplicated successfully', [
        { text: 'OK', onPress: () => router.back() },
      ]);
    } catch {
      Alert.alert('Error', 'Failed to duplicate template');
    } finally {
      setDuplicating(false);
    }
  };

  if (isLoading) return <LoadingSpinner />;
  if (!template) return null;

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle} numberOfLines={1}>
          Template Details
        </Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Card style={styles.infoCard}>
          <View style={styles.titleRow}>
            <Text style={styles.templateName}>{template.template_name}</Text>
            {template.is_global && (
              <View style={styles.globalBadge}>
                <Ionicons name="globe-outline" size={12} color={COLORS.info} />
                <Text style={styles.globalText}>Global</Text>
              </View>
            )}
          </View>
          <Text style={styles.subject}>{template.email_subject}</Text>
          {template.description && (
            <Text style={styles.description}>{template.description}</Text>
          )}
        </Card>

        {/* Meta */}
        <View style={styles.metaGrid}>
          {[
            {
              label: 'Category',
              value: template.category.replace('_', ' '),
              icon: 'pricetag-outline',
            },
            {
              label: 'Version',
              value: `v${template.version ?? 1}`,
              icon: 'git-branch-outline',
            },
            {
              label: 'Usage',
              value: `${template.usage_count ?? 0} times`,
              icon: 'stats-chart-outline',
            },
            {
              label: 'Created',
              value: formatDistanceToNow(new Date(template.created_at), {
                addSuffix: true,
              }),
              icon: 'calendar-outline',
            },
          ].map((item) => (
            <Card key={item.label} style={styles.metaCard}>
              <Ionicons name={item.icon as any} size={16} color={COLORS.textMuted} />
              <Text style={styles.metaLabel}>{item.label}</Text>
              <Text style={styles.metaValue} numberOfLines={2}>
                {item.value}
              </Text>
            </Card>
          ))}
        </View>

        {/* Preview Text */}
        {template.preview_text && (
          <Card style={styles.previewCard}>
            <Text style={styles.sectionLabel}>Preview Text</Text>
            <Text style={styles.previewText}>{template.preview_text}</Text>
          </Card>
        )}

        {/* Email Body Preview */}
        {template.email_body && (
          <Card style={styles.bodyCard}>
            <Text style={styles.sectionLabel}>Email Body (HTML)</Text>
            <Text style={styles.bodyText} numberOfLines={10}>
              {template.email_body
                .replace(/<[^>]*>/g, ' ')
                .replace(/\s+/g, ' ')
                .trim()}
            </Text>
          </Card>
        )}

        {!template.is_global && (
          <Button
            title="Duplicate Template"
            variant="outline"
            onPress={handleDuplicate}
            loading={duplicating}
            style={styles.dupBtn}
            leftIcon={
              <Ionicons name="copy-outline" size={16} color={COLORS.primaryLight} />
            }
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
  backBtn: { padding: 4, width: 40 },
  headerTitle: {
    color: COLORS.text,
    fontSize: 16,
    fontWeight: '600',
    flex: 1,
    textAlign: 'center',
  },
  scroll: { flex: 1 },
  scrollContent: { padding: SPACING.md, paddingBottom: SPACING.xxl },
  infoCard: { marginBottom: SPACING.md },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: SPACING.sm,
  },
  templateName: {
    color: COLORS.text,
    fontSize: 18,
    fontWeight: '700',
    flex: 1,
    marginRight: SPACING.sm,
  },
  globalBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#1e3a5f',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: BORDER_RADIUS.full,
  },
  globalText: { color: COLORS.info, fontSize: 11 },
  subject: { color: COLORS.textMuted, fontSize: 14 },
  description: { color: COLORS.textSecondary, fontSize: 13, marginTop: SPACING.sm },
  metaGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
    marginBottom: SPACING.md,
  },
  metaCard: {
    width: '47%',
    padding: SPACING.sm,
    gap: 4,
    alignItems: 'flex-start',
  },
  metaLabel: { color: COLORS.textMuted, fontSize: 11 },
  metaValue: {
    color: COLORS.text,
    fontSize: 13,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  previewCard: { marginBottom: SPACING.md },
  sectionLabel: {
    color: COLORS.textMuted,
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: SPACING.sm,
  },
  previewText: { color: COLORS.textSecondary, fontSize: 13, lineHeight: 20 },
  bodyCard: { marginBottom: SPACING.md },
  bodyText: { color: COLORS.textSecondary, fontSize: 12, lineHeight: 18 },
  dupBtn: { marginTop: SPACING.sm },
});
