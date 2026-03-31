import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  Alert,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import {
  fetchContactListById,
  fetchContactsByList,
  ContactList,
  Contact,
} from '@/services/contacts';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { COLORS, SPACING, BORDER_RADIUS } from '@/config/constants';
import { formatDistanceToNow } from 'date-fns';

export default function ContactListDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [list, setList] = useState<ContactList | null>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = async () => {
    if (!id) return;
    try {
      const [listData, contactsData] = await Promise.all([
        fetchContactListById(id),
        fetchContactsByList(id),
      ]);
      setList(listData);
      setContacts(contactsData);
    } catch {
      Alert.alert('Error', 'Failed to load contact list');
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  const onRefresh = () => {
    setRefreshing(true);
    load();
  };

  const getStatusVariant = (
    status: string
  ): 'success' | 'danger' | 'secondary' => {
    switch (status?.toLowerCase()) {
      case 'active': return 'success';
      case 'unsubscribed':
      case 'bounced': return 'danger';
      default: return 'secondary';
    }
  };

  const renderContact = ({ item }: { item: Contact }) => (
    <Card style={styles.contactCard}>
      <View style={styles.contactRow}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>
            {item.first_name?.[0]?.toUpperCase() ||
              item.email[0].toUpperCase()}
          </Text>
        </View>
        <View style={styles.contactInfo}>
          <Text style={styles.contactName}>
            {item.first_name && item.last_name
              ? `${item.first_name} ${item.last_name}`
              : item.email}
          </Text>
          {item.first_name && (
            <Text style={styles.contactEmail}>{item.email}</Text>
          )}
          <Text style={styles.contactDate}>
            Added{' '}
            {formatDistanceToNow(new Date(item.created_at), {
              addSuffix: true,
            })}
          </Text>
        </View>
        <Badge label={item.status} variant={getStatusVariant(item.status)} />
      </View>
    </Card>
  );

  if (isLoading) return <LoadingSpinner />;

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle} numberOfLines={1}>
          {list?.name || 'Contact List'}
        </Text>
        <View style={{ width: 40 }} />
      </View>

      {list && (
        <View style={styles.summary}>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryNum}>{list.total_contacts}</Text>
            <Text style={styles.summaryLabel}>Total</Text>
          </View>
          <View style={styles.summaryDivider} />
          <View style={styles.summaryItem}>
            <Text style={[styles.summaryNum, { color: COLORS.success }]}>
              {list.active_contacts}
            </Text>
            <Text style={styles.summaryLabel}>Active</Text>
          </View>
          <View style={styles.summaryDivider} />
          <View style={styles.summaryItem}>
            <Text style={[styles.summaryNum, { color: COLORS.warning }]}>
              {(list.total_contacts || 0) - (list.active_contacts || 0)}
            </Text>
            <Text style={styles.summaryLabel}>Inactive</Text>
          </View>
        </View>
      )}

      <FlatList
        data={contacts}
        keyExtractor={(item) => item.id}
        renderItem={renderContact}
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
            icon="person-outline"
            title="No contacts"
            description="No contacts in this list yet"
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
  summary: {
    flexDirection: 'row',
    backgroundColor: COLORS.surface,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.lg,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  summaryItem: { flex: 1, alignItems: 'center' },
  summaryNum: { color: COLORS.text, fontSize: 24, fontWeight: '700' },
  summaryLabel: { color: COLORS.textMuted, fontSize: 12, marginTop: 2 },
  summaryDivider: { width: 1, backgroundColor: COLORS.border },
  list: { padding: SPACING.md, gap: SPACING.sm, paddingBottom: SPACING.xxl },
  contactCard: {},
  contactRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.primary + '40',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    color: COLORS.primaryLight,
    fontSize: 16,
    fontWeight: '700',
  },
  contactInfo: { flex: 1 },
  contactName: { color: COLORS.text, fontSize: 14, fontWeight: '600' },
  contactEmail: { color: COLORS.textMuted, fontSize: 12, marginTop: 1 },
  contactDate: { color: COLORS.textMuted, fontSize: 11, marginTop: 2 },
});
