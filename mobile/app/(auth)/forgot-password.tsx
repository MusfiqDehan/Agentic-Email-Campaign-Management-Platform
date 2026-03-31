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
import { useRouter } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import { requestPasswordReset } from '@/services/auth';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { COLORS, SPACING } from '@/config/constants';

export default function ForgotPasswordScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Please enter a valid email address');
      return;
    }
    setIsLoading(true);
    try {
      await requestPasswordReset({ email });
      setSent(true);
    } catch {
      Alert.alert('Error', 'Failed to send reset email. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (sent) {
    return (
      <View style={styles.container}>
        <StatusBar style="light" />
        <View style={styles.successContainer}>
          <View style={styles.successIcon}>
            <Ionicons name="mail-open-outline" size={40} color={COLORS.success} />
          </View>
          <Text style={styles.successTitle}>Check your email</Text>
          <Text style={styles.successText}>
            We've sent a password reset link to {email}
          </Text>
          <Button
            title="Back to Login"
            onPress={() => router.replace('/(auth)/login')}
            style={styles.btn}
          />
        </View>
      </View>
    );
  }

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

        <View style={styles.iconWrapper}>
          <Ionicons name="key-outline" size={40} color={COLORS.primaryLight} />
        </View>

        <Text style={styles.title}>Forgot password?</Text>
        <Text style={styles.subtitle}>
          Enter your email and we'll send you a reset link.
        </Text>

        <Input
          label="Email"
          placeholder="you@example.com"
          value={email}
          onChangeText={(v) => {
            setEmail(v);
            setError('');
          }}
          keyboardType="email-address"
          autoCapitalize="none"
          error={error}
          leftIcon={<Ionicons name="mail-outline" size={18} color={COLORS.textMuted} />}
        />

        <Button
          title="Send Reset Link"
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
  iconWrapper: {
    alignItems: 'center',
    marginBottom: SPACING.lg,
  },
  title: {
    color: COLORS.text,
    fontSize: 26,
    fontWeight: '700',
    marginBottom: SPACING.sm,
  },
  subtitle: {
    color: COLORS.textMuted,
    fontSize: 14,
    lineHeight: 20,
    marginBottom: SPACING.xl,
  },
  btn: { marginTop: SPACING.sm },
  successContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: SPACING.xl,
  },
  successIcon: {
    backgroundColor: '#166534',
    borderRadius: 50,
    padding: SPACING.lg,
    marginBottom: SPACING.lg,
  },
  successTitle: {
    color: COLORS.text,
    fontSize: 24,
    fontWeight: '700',
    marginBottom: SPACING.sm,
  },
  successText: {
    color: COLORS.textMuted,
    fontSize: 14,
    textAlign: 'center',
    marginBottom: SPACING.xl,
  },
});
