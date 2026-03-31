import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Alert,
  KeyboardAvoidingView,
  Platform,
  TouchableOpacity,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import { resetPassword } from '@/services/auth';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { COLORS, SPACING } from '@/config/constants';

export default function ResetPasswordScreen() {
  const router = useRouter();
  const { token } = useLocalSearchParams<{ token: string }>();

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<{ password?: string; confirmPassword?: string }>({});

  const validate = () => {
    const e: typeof errors = {};
    if (!password || password.length < 8) e.password = 'Password must be at least 8 characters';
    if (password !== confirmPassword) e.confirmPassword = "Passwords don't match";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;
    if (!token) {
      Alert.alert('Error', 'Invalid reset token');
      return;
    }
    setIsLoading(true);
    try {
      await resetPassword({ token, new_password: password });
      Alert.alert('Success', 'Password reset successfully!', [
        { text: 'Login', onPress: () => router.replace('/(auth)/login') },
      ]);
    } catch {
      Alert.alert('Error', 'Failed to reset password. The link may be expired.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <StatusBar style="light" />
      <ScrollView
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled"
      >
        <TouchableOpacity style={styles.back} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>

        <Text style={styles.title}>Reset password</Text>
        <Text style={styles.subtitle}>Enter your new password below.</Text>

        <Input
          label="New Password"
          placeholder="Min 8 characters"
          value={password}
          onChangeText={setPassword}
          secureTextEntry={!showPassword}
          error={errors.password}
          leftIcon={<Ionicons name="lock-closed-outline" size={18} color={COLORS.textMuted} />}
          rightIcon={
            <Ionicons
              name={showPassword ? 'eye-off-outline' : 'eye-outline'}
              size={18}
              color={COLORS.textMuted}
            />
          }
          onRightIconPress={() => setShowPassword(!showPassword)}
        />

        <Input
          label="Confirm Password"
          placeholder="Re-enter password"
          value={confirmPassword}
          onChangeText={setConfirmPassword}
          secureTextEntry={!showConfirm}
          error={errors.confirmPassword}
          leftIcon={<Ionicons name="shield-checkmark-outline" size={18} color={COLORS.textMuted} />}
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
          title="Reset Password"
          onPress={handleSubmit}
          loading={isLoading}
          style={styles.btn}
        />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  scroll: {
    flexGrow: 1,
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.xl,
  },
  back: { marginBottom: SPACING.xl },
  title: {
    color: COLORS.text,
    fontSize: 26,
    fontWeight: '700',
    marginBottom: SPACING.sm,
  },
  subtitle: {
    color: COLORS.textMuted,
    fontSize: 14,
    marginBottom: SPACING.xl,
  },
  btn: { marginTop: SPACING.sm },
});
