import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SPACING } from '@/config/constants';

export default function VerifyEmailScreen() {
  const router = useRouter();
  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      <View style={styles.iconWrapper}>
        <Ionicons name="mail-open-outline" size={56} color={COLORS.primaryLight} />
      </View>
      <Text style={styles.title}>Verify your email</Text>
      <Text style={styles.text}>
        A verification link has been sent to your email address. Please click the
        link to verify your account before signing in.
      </Text>
      <TouchableOpacity onPress={() => router.replace('/(auth)/login')}>
        <Text style={styles.link}>Back to Login</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    alignItems: 'center',
    justifyContent: 'center',
    padding: SPACING.xl,
  },
  iconWrapper: {
    backgroundColor: COLORS.surface,
    borderRadius: 50,
    padding: SPACING.xl,
    marginBottom: SPACING.xl,
  },
  title: {
    color: COLORS.text,
    fontSize: 26,
    fontWeight: '700',
    marginBottom: SPACING.md,
    textAlign: 'center',
  },
  text: {
    color: COLORS.textMuted,
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: SPACING.xl,
  },
  link: {
    color: COLORS.primaryLight,
    fontSize: 15,
    fontWeight: '600',
  },
});
