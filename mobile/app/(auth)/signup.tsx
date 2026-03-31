import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Link, useRouter } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '@/contexts/AuthContext';
import { signup as signupService } from '@/services/auth';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { COLORS, SPACING, BORDER_RADIUS } from '@/config/constants';

export default function SignupScreen() {
  const router = useRouter();
  const { login } = useAuth();

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    username: '',
    email: '',
    organization_name: '',
    password: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const setValue = (key: string, value: string) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
    if (errors[key]) setErrors((prev) => ({ ...prev, [key]: '' }));
  };

  const validate = () => {
    const e: Record<string, string> = {};
    if (!formData.first_name) e.first_name = 'First name is required';
    if (!formData.last_name) e.last_name = 'Last name is required';
    if (!formData.username || formData.username.length < 3)
      e.username = 'Username must be at least 3 characters';
    if (!formData.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email))
      e.email = 'Valid email is required';
    if (!formData.organization_name) e.organization_name = 'Organization name is required';
    if (!formData.password || formData.password.length < 8)
      e.password = 'Password must be at least 8 characters';
    if (formData.password !== formData.confirmPassword)
      e.confirmPassword = "Passwords don't match";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSignup = async () => {
    if (!validate()) return;
    setIsLoading(true);
    try {
      const data = await signupService({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        first_name: formData.first_name,
        last_name: formData.last_name,
        organization_name: formData.organization_name,
        terms_accepted: true,
      });

      if (data?.access) {
        await login(data.access, data.refresh, data.user);
        router.replace('/(tabs)/dashboard');
      } else {
        Alert.alert(
          'Account Created',
          'Please check your email to verify your account.',
          [{ text: 'OK', onPress: () => router.replace('/(auth)/login') }]
        );
      }
    } catch (error: any) {
      const msg =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        'Failed to create account';
      Alert.alert('Signup Failed', msg);
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
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* Logo */}
        <View style={styles.logoSection}>
          <LinearGradient
            colors={[COLORS.primary, COLORS.primaryLight]}
            style={styles.logoIcon}
          >
            <Ionicons name="mail" size={28} color={COLORS.white} />
          </LinearGradient>
          <Text style={styles.appName}>EmailCampaign</Text>
        </View>

        <Text style={styles.title}>Create account</Text>
        <Text style={styles.subtitle}>Start your email campaign journey</Text>

        {/* Form */}
        <View style={styles.form}>
          <View style={styles.row}>
            <View style={styles.flex}>
              <Input
                label="First Name"
                placeholder="John"
                value={formData.first_name}
                onChangeText={(v) => setValue('first_name', v)}
                error={errors.first_name}
              />
            </View>
            <View style={styles.flex}>
              <Input
                label="Last Name"
                placeholder="Doe"
                value={formData.last_name}
                onChangeText={(v) => setValue('last_name', v)}
                error={errors.last_name}
              />
            </View>
          </View>

          <Input
            label="Username"
            placeholder="johndoe"
            value={formData.username}
            onChangeText={(v) => setValue('username', v)}
            autoCapitalize="none"
            error={errors.username}
            leftIcon={<Ionicons name="person-outline" size={18} color={COLORS.textMuted} />}
          />

          <Input
            label="Email"
            placeholder="you@example.com"
            value={formData.email}
            onChangeText={(v) => setValue('email', v)}
            keyboardType="email-address"
            autoCapitalize="none"
            error={errors.email}
            leftIcon={<Ionicons name="mail-outline" size={18} color={COLORS.textMuted} />}
          />

          <Input
            label="Organization Name"
            placeholder="Acme Corp"
            value={formData.organization_name}
            onChangeText={(v) => setValue('organization_name', v)}
            error={errors.organization_name}
            leftIcon={<Ionicons name="business-outline" size={18} color={COLORS.textMuted} />}
          />

          <Input
            label="Password"
            placeholder="Min 8 characters"
            value={formData.password}
            onChangeText={(v) => setValue('password', v)}
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
            value={formData.confirmPassword}
            onChangeText={(v) => setValue('confirmPassword', v)}
            secureTextEntry={!showConfirmPassword}
            error={errors.confirmPassword}
            leftIcon={<Ionicons name="shield-checkmark-outline" size={18} color={COLORS.textMuted} />}
            rightIcon={
              <Ionicons
                name={showConfirmPassword ? 'eye-off-outline' : 'eye-outline'}
                size={18}
                color={COLORS.textMuted}
              />
            }
            onRightIconPress={() => setShowConfirmPassword(!showConfirmPassword)}
          />

          <Button
            title="Create Account"
            onPress={handleSignup}
            loading={isLoading}
            style={styles.submitBtn}
          />
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>Already have an account? </Text>
          <Link href="/(auth)/login" asChild>
            <TouchableOpacity>
              <Text style={styles.footerLink}>Sign in</Text>
            </TouchableOpacity>
          </Link>
        </View>
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
  logoSection: {
    alignItems: 'center',
    marginBottom: SPACING.lg,
  },
  logoIcon: {
    width: 56,
    height: 56,
    borderRadius: BORDER_RADIUS.lg,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: SPACING.sm,
  },
  appName: { color: COLORS.text, fontSize: 20, fontWeight: '700' },
  title: {
    color: COLORS.text,
    fontSize: 26,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: SPACING.xs,
  },
  subtitle: {
    color: COLORS.textMuted,
    fontSize: 14,
    textAlign: 'center',
    marginBottom: SPACING.lg,
  },
  form: { gap: 4 },
  row: { flexDirection: 'row', gap: SPACING.sm },
  flex: { flex: 1 },
  submitBtn: { marginTop: SPACING.sm },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: SPACING.xl,
    paddingBottom: SPACING.lg,
  },
  footerText: { color: COLORS.textMuted, fontSize: 14 },
  footerLink: { color: COLORS.primaryLight, fontSize: 14, fontWeight: '600' },
});
