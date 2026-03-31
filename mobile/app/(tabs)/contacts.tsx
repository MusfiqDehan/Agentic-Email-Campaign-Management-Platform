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
  Modal,
} from 'react-native';
import { useRouter } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import {
  fetchContactLists,
  createContactList,
  updateContactList,
  deleteContactList,
  ContactList,
} from '@/services/contacts';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { COLORS, SPACING, BORDER_RADIUS } from '@/config/constants';
import { formatDistanceToNow } from 'date-fns';

export default function ContactsScreen() {
  const router = useRouter();
  const [lists, setLists] = useState<ContactList[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');

  // Create modal
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [createErrors, setCreateErrors] = useState<{ name?: string }>({});

  // Edit modal
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editList, setEditList] = useState<ContactList | null>(null);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await fetchContactLists();
      setLists(data);
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

  const handleCreate = async () => {
    if (!newName.trim()) {
      setCreateErrors({ name: 'Name is required' });
      return;
    }
    setIsCreating(true);
    try {
      const created = await createContactList({
        name: newName.trim(),
        description: newDesc.trim(),
      });
      setLists((prev) => [created, ...prev]);
      setCreateModalVisible(false);
      setNewName('');
      setNewDesc('');
    } catch {
      Alert.alert('Error', 'Failed to create contact list');
    } finally {
      setIsCreating(false);
    }
  };

  const openEdit = (list: ContactList) => {
    setEditList(list);
    setEditName(list.name);
    setEditDesc(list.description || '');
    setEditModalVisible(true);
  };

  const handleUpdate = async () => {
    if (!editList || !editName.trim()) return;
    setIsUpdating(true);
    try {
      const updated = await updateContactList(editList.id, {
        name: editName.trim(),
        description: editDesc.trim(),
      });
      setLists((prev) =>
        prev.map((l) => (l.id === editList.id ? { ...l, ...updated } : l))
      );
      setEditModalVisible(false);
    } catch {
      Alert.alert('Error', 'Failed to update contact list');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDelete = (list: ContactList) => {
    Alert.alert('Delete List', `Delete "${list.name}"? This cannot be undone.`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            await deleteContactList(list.id);
            setLists((prev) => prev.filter((l) => l.id !== list.id));
          } catch {
            Alert.alert('Error', 'Failed to delete list');
          }
        },
      },
    ]);
  };

  const filtered = lists.filter((l) =>
    l.name.toLowerCase().includes(search.toLowerCase())
  );

  const renderItem = ({ item }: { item: ContactList }) => (
    <Card style={styles.card}>
      <TouchableOpacity
        activeOpacity={0.8}
        onPress={() => router.push(`/(tabs)/contact-list/${item.id}` as any)}
      >
        <View style={styles.cardHeader}>
          <View style={styles.iconWrapper}>
            <Ionicons name="people" size={20} color={COLORS.primaryLight} />
          </View>
          <View style={styles.cardInfo}>
            <Text style={styles.cardTitle} numberOfLines={1}>
              {item.name}
            </Text>
            {item.description && (
              <Text style={styles.cardDesc} numberOfLines={1}>
                {item.description}
              </Text>
            )}
          </View>
        </View>
        <View style={styles.cardStats}>
          <View style={styles.statBadge}>
            <Text style={styles.statNum}>{item.total_contacts ?? 0}</Text>
            <Text style={styles.statLabel}>Total</Text>
          </View>
          <View style={styles.statBadge}>
            <Text style={[styles.statNum, { color: COLORS.success }]}>
              {item.active_contacts ?? 0}
            </Text>
            <Text style={styles.statLabel}>Active</Text>
          </View>
          <Text style={styles.cardDate}>
            {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}
          </Text>
        </View>
      </TouchableOpacity>
      <View style={styles.actions}>
        <TouchableOpacity style={styles.actionBtn} onPress={() => openEdit(item)}>
          <Ionicons name="pencil-outline" size={18} color={COLORS.primaryLight} />
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionBtn} onPress={() => handleDelete(item)}>
          <Ionicons name="trash-outline" size={18} color={COLORS.error} />
        </TouchableOpacity>
      </View>
    </Card>
  );

  if (isLoading) return <LoadingSpinner />;

  return (
    <View style={styles.container}>
      <StatusBar style="light" />

      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Contacts</Text>
          <Text style={styles.subtitle}>Manage your contact lists</Text>
        </View>
        <TouchableOpacity
          style={styles.addBtn}
          onPress={() => setCreateModalVisible(true)}
        >
          <Ionicons name="add" size={22} color={COLORS.white} />
        </TouchableOpacity>
      </View>

      {/* Search */}
      <View style={styles.searchContainer}>
        <View style={styles.searchWrapper}>
          <Ionicons name="search-outline" size={18} color={COLORS.textMuted} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search lists..."
            placeholderTextColor={COLORS.textMuted}
            value={search}
            onChangeText={setSearch}
          />
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
            icon="people-outline"
            title="No contact lists"
            description="Create a contact list to organize your subscribers"
          >
            <Button
              title="Create List"
              onPress={() => setCreateModalVisible(true)}
              size="sm"
              style={{ marginTop: SPACING.md }}
            />
          </EmptyState>
        }
      />

      {/* Create Modal */}
      <Modal
        visible={createModalVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setCreateModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modal}>
            <Text style={styles.modalTitle}>New Contact List</Text>
            <Input
              label="Name *"
              placeholder="e.g. Newsletter Subscribers"
              value={newName}
              onChangeText={(v) => {
                setNewName(v);
                setCreateErrors({});
              }}
              error={createErrors.name}
            />
            <Input
              label="Description"
              placeholder="Optional description"
              value={newDesc}
              onChangeText={setNewDesc}
              multiline
            />
            <View style={styles.modalActions}>
              <Button
                title="Cancel"
                variant="outline"
                onPress={() => setCreateModalVisible(false)}
                style={styles.modalBtn}
              />
              <Button
                title="Create"
                onPress={handleCreate}
                loading={isCreating}
                style={styles.modalBtn}
              />
            </View>
          </View>
        </View>
      </Modal>

      {/* Edit Modal */}
      <Modal
        visible={editModalVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setEditModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modal}>
            <Text style={styles.modalTitle}>Edit Contact List</Text>
            <Input
              label="Name *"
              placeholder="List name"
              value={editName}
              onChangeText={setEditName}
            />
            <Input
              label="Description"
              placeholder="Optional description"
              value={editDesc}
              onChangeText={setEditDesc}
              multiline
            />
            <View style={styles.modalActions}>
              <Button
                title="Cancel"
                variant="outline"
                onPress={() => setEditModalVisible(false)}
                style={styles.modalBtn}
              />
              <Button
                title="Update"
                onPress={handleUpdate}
                loading={isUpdating}
                style={styles.modalBtn}
              />
            </View>
          </View>
        </View>
      </Modal>
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
  addBtn: {
    backgroundColor: COLORS.primary,
    width: 40,
    height: 40,
    borderRadius: BORDER_RADIUS.full,
    alignItems: 'center',
    justifyContent: 'center',
  },
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
  card: {},
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: SPACING.sm,
    marginBottom: SPACING.sm,
  },
  iconWrapper: {
    width: 40,
    height: 40,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.primary + '20',
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardInfo: { flex: 1 },
  cardTitle: { color: COLORS.text, fontSize: 15, fontWeight: '600' },
  cardDesc: { color: COLORS.textMuted, fontSize: 13, marginTop: 2 },
  cardStats: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.md,
    marginTop: SPACING.sm,
  },
  statBadge: {
    backgroundColor: COLORS.surfaceLight,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: BORDER_RADIUS.sm,
    alignItems: 'center',
  },
  statNum: { color: COLORS.text, fontSize: 14, fontWeight: '700' },
  statLabel: { color: COLORS.textMuted, fontSize: 10 },
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
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'flex-end',
  },
  modal: {
    backgroundColor: COLORS.surface,
    borderTopLeftRadius: BORDER_RADIUS.xl,
    borderTopRightRadius: BORDER_RADIUS.xl,
    padding: SPACING.lg,
    paddingBottom: SPACING.xxl,
  },
  modalTitle: {
    color: COLORS.text,
    fontSize: 18,
    fontWeight: '700',
    marginBottom: SPACING.lg,
  },
  modalActions: {
    flexDirection: 'row',
    gap: SPACING.sm,
    marginTop: SPACING.sm,
  },
  modalBtn: { flex: 1 },
});
