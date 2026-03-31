import { Redirect } from 'expo-router';
import { useAuth } from '@/contexts/AuthContext';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export default function Index() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) return <LoadingSpinner message="Starting up..." />;
  if (isAuthenticated) return <Redirect href="/(tabs)/dashboard" />;
  return <Redirect href="/(auth)/login" />;
}
