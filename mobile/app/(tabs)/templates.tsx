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
  fetchTemplates,
  deleteTemplate,
  duplicateTemplate,
  Template,
} from '@/services/templates';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { COLORS, SPACING, BORDER_RADIUS } from '@/config/constants';
import { formatDistanceToNow } from 'date-fns';

const CATEGORY_COLORS: Record<string, { bg: string; text: string }> = {
  welcome: { bg: '#1e3a5f', text: '#93c5fd' },
  newsletter: { bg: '#4c1d95', text: '#ddd6fe' },
  promotional: { bg: '#166534', text: '#86efac' },
  transactional: { bg: '#92400e', text: '#fde68a' },
  follow_up: { bg: '#9a3412', text: '#fdba74' },
  event: { bg: '#1e3a5f', text: '#a5b4fc' },
  announcement: { bg: '#831843', text: '#f9a8d4' },
  other: { bg: '#334155', text: '#cbd5e1' },
};

export default function TemplatesScreen() {
  const router = useRouter();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');
  const [activeTab, setActiveTab] = useState<'all' | 'global' | 'org'>('all');

  const load = useCallback(async () => {
    try {
      const data = await fetchTemplates();
      setTemplates(data);
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

  const handleDelete = (template: Template) => {
    Alert.alert(
      'Delete Template',
      `Delete "${template.template_name}"? This cannot be undone.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await deleteTemplate(template.id);
              setTemplates((prev) => prev.filter((t) => t.id !== template.id));
            } catch {
              Alert.alert('Error', 'Failed to delete template');
            }
          },
        },
      ]
    );
  };

  const handleDuplicate = async (template: Template) => {
    try {
      const duplicated = await duplicateTemplate(template.id);
      setTemplates((prev) => [duplicated, ...prev]);
      Alert.alert('Success', 'Template duplicated successfully');
    } catch {
      Alert.alert('Error', 'Failed to duplicate template');
    }
  };

  const filtered = templates.filter((t) => {
    const matchesSearch =
      t.template_name.toLowerCase().includes(search.toLowerCase()) ||
      t.email_subject.toLowerCase().includes(search.toLowerCase());
    const matchesTab =
      activeTab === 'all' ||
      (activeTab === 'global' && t.is_global) ||
      (activeTab === 'org' && !t.is_global);
    return matchesSearch && matchesTab;
  });

  const renderItem = ({ item }: { item: Template }) => {
    const catColor = CATEGORY_COLORS[item.category] || CATEGORY_COLORS.other;
    return (
      <Card style={styles.card}>
        <TouchableOpacity
          activeOpacity={0.8}
          onPress={() => router.push(`/(tabs)/template/${item.id}` as any)}
        >
          <View style={styles.cardHeader}>
            <View style={styles.cardInfo}>
              <Text style={styles.cardTitle} numberOfLines={1}>
                {item.template_name}
              </Text>
              <Text style={styles.cardSubject} numberOfLines={1}>
                {item.email_subject}
              </Text>
            </View>
            <View
              style={[
                styles.catBadge,
                { backgroundColor: catColor.bg },
              ]}
            >
              <Text style={[styles.catBadgeText, { color: catColor.text }]}>
                {item.category.replace('_', ' ')}
              </Text>
            </View>
          </View>

          <View style={styles.cardMeta}>
            {item.is_global && (
              <View style={styles.globalBadge}>
                <Ionicons name="globe-outline" size={12} color={COLORS.info} />
                <Text style={styles.globalText}>Global</Text>
              </View>
            )}
            {item.usage_count !== undefined && (
              <View style={styles.usageBadge}>
                <Ionicons name="stats-chart-outline" size={12} color={COLORS.textMuted} />
                <Text style={styles.usageText}>{item.usage_count} uses</Text>
              </View>
            )}
            <Text style={styles.cardDate}>
              {formatDistanceToNow(new Date(item.created_at), {
                addSuffix: true,
              })}
            </Text>
          </View>
        </TouchableOpacity>

        <View style={styles.actions}>
          <TouchableOpacity
            style={styles.actionBtn}
            onPress={() => handleDuplicate(item)}
          >
            <Ionicons name="copy-outline" size={18} color={COLORS.primaryLight} />
          </TouchableOpacity>
          {!item.is_global && (
            <TouchableOpacity
              style={styles.actionBtn}
              onPress={() => handleDelete(item)}
            >
              <Ionicons name="trash-outline" size={18} color={COLORS.error} />
            </TouchableOpacity>
          )}
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
          <Text style={styles.title}>Templates</Text>
          <Text style={styles.subtitle}>
            {templates.length} template{templates.length !== 1 ? 's' : ''}
          </Text>
        </View>
      </View>

      {/* Search */}
      <View style={styles.searchContainer}>
        <View style={styles.searchWrapper}>
          <Ionicons name="search-outline" size={18} color={COLORS.textMuted} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search templates..."
            placeholderTextColor={COLORS.textMuted}
            value={search}
            onChangeText={setSearch}
          />
        </View>
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        {(['all', 'global', 'org'] as const).map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.tabActive]}
            onPress={() => setActiveTab(tab)}
          >
            <Text
              style={[
                styles.tabText,
                activeTab === tab && styles.tabTextActive,
              ]}
            >
              {tab === 'all' ? 'All' : tab === 'global' ? 'Global' : 'My Org'}
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
            icon="document-text-outline"
            title="No templates found"
            description={
              search ? 'No templates match your search' : 'No templates available'
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
  subtitle: { color: COLORS.textMuted, fontSize: 13, marginTop: 2 },
  searchContainer: {
    padding: SPACING.md,
    paddingBottom: 0,
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
  tabs: {
    flexDirection: 'row',
    backgroundColor: COLORS.surface,
    paddingHorizontal: SPACING.md,
    paddingBottom: SPACING.sm,
    paddingTop: SPACING.sm,
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
  card: {},
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: SPACING.sm,
  },
  cardInfo: { flex: 1, marginRight: SPACING.sm },
  cardTitle: { color: COLORS.text, fontSize: 15, fontWeight: '600' },
  cardSubject: { color: COLORS.textMuted, fontSize: 13, marginTop: 2 },
  catBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: BORDER_RADIUS.full,
  },
  catBadgeText: { fontSize: 11, fontWeight: '600', textTransform: 'capitalize' },
  cardMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    flexWrap: 'wrap',
  },
  globalBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#1e3a5f',
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: BORDER_RADIUS.full,
  },
  globalText: { color: COLORS.info, fontSize: 11 },
  usageBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  usageText: { color: COLORS.textMuted, fontSize: 11 },
  cardDate: { color: COLORS.textMuted, fontSize: 11, marginLeft: 'auto' },
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
