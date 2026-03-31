import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  RefreshControl,
  Image,
  TextInput,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { useAuth } from '@/contexts/AuthContext';
import { fetchProfile, updateProfile, ProfileData } from '@/services/profile';
import { changePassword, reauthenticate } from '@/services/auth';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { COLORS, SPACING, BORDER_RADIUS } from '@/config/constants';

export default function ProfileScreen() {
  const { user, logout, login, refreshUser } = useAuth();
  const [profileData, setProfileData] = useState<ProfileData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'profile' | 'password' | 'team'>('profile');

  // Password change
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [changingPassword, setChangingPassword] = useState(false);
  const [showOld, setShowOld] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const load = async () => {
    try {
      const data = await fetchProfile();
      setProfileData(data);
    } catch {
      Alert.alert('Error', 'Failed to load profile');
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    load();
  };

  const handlePickImage = async () => {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert('Permission required', 'Allow access to your photo library to upload a profile picture.');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0]) {
      const asset = result.assets[0];
      const fd = new FormData();
      fd.append('profile_picture', {
        uri: asset.uri,
        type: 'image/jpeg',
        name: 'profile.jpg',
      } as any);
      try {
        await updateProfile(fd);
        await refreshUser();
        await load();
      } catch {
        Alert.alert('Error', 'Failed to update profile picture');
      }
    }
  };

  const handleSaveProfile = async () => {
    if (!profileData) return;
    setIsSaving(true);
    try {
      const fd = new FormData();
      fd.append('first_name', profileData.first_name);
      fd.append('last_name', profileData.last_name);
      fd.append('phone_number', profileData.phone_number || '');
      fd.append('occupation', profileData.occupation || '');
      fd.append('country', profileData.country || '');
      fd.append('city', profileData.city || '');
      fd.append('address', profileData.address || '');
      await updateProfile(fd);
      await refreshUser();
      Alert.alert('Success', 'Profile updated successfully');
    } catch {
      Alert.alert('Error', 'Failed to update profile');
    } finally {
      setIsSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (!newPassword || newPassword.length < 8) {
      Alert.alert('Error', 'New password must be at least 8 characters');
      return;
    }
    if (newPassword !== confirmPassword) {
      Alert.alert('Error', "Passwords don't match");
      return;
    }
    if (!user?.email) return;

    setChangingPassword(true);
    try {
      await changePassword({ old_password: oldPassword, new_password: newPassword });
      const authResponse = await reauthenticate(user.email, newPassword);
      await login(authResponse.access, authResponse.refresh, authResponse.user);
      Alert.alert('Success', 'Password changed successfully');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch {
      Alert.alert('Error', 'Failed to change password. Check your current password.');
    } finally {
      setChangingPassword(false);
    }
  };

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure you want to logout?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Logout',
        style: 'destructive',
        onPress: logout,
      },
    ]);
  };

  if (isLoading) return <LoadingSpinner />;

  const avatarLetter = profileData?.first_name?.[0]?.toUpperCase() || 'U';

  return (
    <View style={styles.container}>
      <StatusBar style="light" />

      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Profile</Text>
        <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={22} color={COLORS.error} />
        </TouchableOpacity>
      </View>

      {/* Avatar */}
      <View style={styles.avatarSection}>
        <TouchableOpacity style={styles.avatarWrapper} onPress={handlePickImage}>
          {profileData?.profile_picture ? (
            <Image
              source={{ uri: profileData.profile_picture }}
              style={styles.avatarImage}
            />
          ) : (
            <View style={styles.avatarFallback}>
              <Text style={styles.avatarText}>{avatarLetter}</Text>
            </View>
          )}
          <View style={styles.cameraOverlay}>
            <Ionicons name="camera" size={14} color={COLORS.white} />
          </View>
        </TouchableOpacity>
        <Text style={styles.userName}>
          {profileData?.first_name} {profileData?.last_name}
        </Text>
        <Text style={styles.userEmail}>{profileData?.email}</Text>
        {profileData?.organization_details?.name && (
          <View style={styles.orgBadge}>
            <Ionicons name="business-outline" size={12} color={COLORS.textMuted} />
            <Text style={styles.orgName}>{profileData.organization_details.name}</Text>
          </View>
        )}
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        {(['profile', 'password'] as const).map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab && styles.tabActive]}
            onPress={() => setActiveTab(tab)}
          >
            <Text style={[styles.tabText, activeTab === tab && styles.tabTextActive]}>
              {tab === 'profile' ? 'Profile' : 'Security'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

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
        {activeTab === 'profile' && profileData && (
          <View style={styles.form}>
            <View style={styles.row}>
              <View style={styles.flex}>
                <Input
                  label="First Name"
                  value={profileData.first_name}
                  onChangeText={(v) =>
                    setProfileData({ ...profileData, first_name: v })
                  }
                />
              </View>
              <View style={styles.flex}>
                <Input
                  label="Last Name"
                  value={profileData.last_name}
                  onChangeText={(v) =>
                    setProfileData({ ...profileData, last_name: v })
                  }
                />
              </View>
            </View>
            <Input
              label="Email"
              value={profileData.email}
              editable={false}
              containerStyle={styles.disabledInput}
            />
            <Input
              label="Phone"
              value={profileData.phone_number || ''}
              onChangeText={(v) =>
                setProfileData({ ...profileData, phone_number: v })
              }
              keyboardType="phone-pad"
            />
            <Input
              label="Occupation"
              value={profileData.occupation || ''}
              onChangeText={(v) =>
                setProfileData({ ...profileData, occupation: v })
              }
            />
            <View style={styles.row}>
              <View style={styles.flex}>
                <Input
                  label="Country"
                  value={profileData.country || ''}
                  onChangeText={(v) =>
                    setProfileData({ ...profileData, country: v })
                  }
                />
              </View>
              <View style={styles.flex}>
                <Input
                  label="City"
                  value={profileData.city || ''}
                  onChangeText={(v) =>
                    setProfileData({ ...profileData, city: v })
                  }
                />
              </View>
            </View>
            <Input
              label="Address"
              value={profileData.address || ''}
              onChangeText={(v) =>
                setProfileData({ ...profileData, address: v })
              }
              multiline
            />
            <Button
              title="Save Changes"
              onPress={handleSaveProfile}
              loading={isSaving}
            />
          </View>
        )}

        {activeTab === 'password' && (
          <View style={styles.form}>
            <Card style={styles.infoCard}>
              <Ionicons name="shield-checkmark-outline" size={20} color={COLORS.info} />
              <Text style={styles.infoText}>
                Choose a strong password with at least 8 characters.
              </Text>
            </Card>
            <Input
              label="Current Password"
              value={oldPassword}
              onChangeText={setOldPassword}
              secureTextEntry={!showOld}
              rightIcon={
                <Ionicons
                  name={showOld ? 'eye-off-outline' : 'eye-outline'}
                  size={18}
                  color={COLORS.textMuted}
                />
              }
              onRightIconPress={() => setShowOld(!showOld)}
            />
            <Input
              label="New Password"
              value={newPassword}
              onChangeText={setNewPassword}
              secureTextEntry={!showNew}
              rightIcon={
                <Ionicons
                  name={showNew ? 'eye-off-outline' : 'eye-outline'}
                  size={18}
                  color={COLORS.textMuted}
                />
              }
              onRightIconPress={() => setShowNew(!showNew)}
            />
            <Input
              label="Confirm New Password"
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              secureTextEntry={!showConfirm}
              rightIcon={
                <Ionicons
                  name={showConfirm ? 'eye-off-outline' : 'eye-outline'}
                  size={18}
                  color={COLORS.textMuted}
                />
              }
              onRightIconPress={() => setShowConfirm(!showConfirm)}
            />
            <Button
              title="Change Password"
              onPress={handleChangePassword}
              loading={changingPassword}
            />
          </View>
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
    paddingBottom: SPACING.md,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  title: { color: COLORS.text, fontSize: 24, fontWeight: '700' },
  logoutBtn: {
    padding: 8,
    backgroundColor: COLORS.surfaceLight,
    borderRadius: BORDER_RADIUS.md,
  },
  avatarSection: {
    alignItems: 'center',
    padding: SPACING.lg,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  avatarWrapper: {
    position: 'relative',
    marginBottom: SPACING.sm,
  },
  avatarImage: {
    width: 80,
    height: 80,
    borderRadius: 40,
  },
  avatarFallback: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { color: COLORS.white, fontSize: 32, fontWeight: '700' },
  cameraOverlay: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    width: 24,
    height: 24,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: COLORS.surface,
  },
  userName: { color: COLORS.text, fontSize: 18, fontWeight: '700' },
  userEmail: { color: COLORS.textMuted, fontSize: 13, marginTop: 2 },
  orgBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: SPACING.sm,
    backgroundColor: COLORS.surfaceLight,
    paddingHorizontal: SPACING.sm,
    paddingVertical: 4,
    borderRadius: BORDER_RADIUS.full,
  },
  orgName: { color: COLORS.textMuted, fontSize: 12 },
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
    flex: 1,
    paddingVertical: 8,
    borderRadius: BORDER_RADIUS.md,
    backgroundColor: COLORS.surfaceLight,
    alignItems: 'center',
  },
  tabActive: { backgroundColor: COLORS.primary },
  tabText: { color: COLORS.textMuted, fontSize: 13, fontWeight: '500' },
  tabTextActive: { color: COLORS.white, fontWeight: '600' },
  scroll: { flex: 1 },
  scrollContent: { padding: SPACING.md, paddingBottom: SPACING.xxl },
  form: { gap: 4 },
  row: { flexDirection: 'row', gap: SPACING.sm },
  flex: { flex: 1 },
  disabledInput: { opacity: 0.6 },
  infoCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    marginBottom: SPACING.md,
    backgroundColor: '#1e3a5f30',
    borderColor: '#1e3a5f',
  },
  infoText: { color: COLORS.textSecondary, fontSize: 13, flex: 1, lineHeight: 18 },
});
