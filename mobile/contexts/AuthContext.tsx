import React, { createContext, useContext, useState, useEffect } from 'react';
import * as SecureStore from 'expo-secure-store';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '@/config/axios';

export interface Organization {
  id: string;
  name: string;
  slug?: string;
  is_owner?: boolean;
  is_admin?: boolean;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  profile_picture?: string;
  is_org_admin?: boolean;
  is_platform_admin?: boolean;
  organization?: Organization;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, refreshToken: string, user: User) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const token = await SecureStore.getItemAsync('access_token');
        if (token) {
          const storedUser = await AsyncStorage.getItem('user');
          if (storedUser) {
            setUser(JSON.parse(storedUser));
          }
        }
      } catch {
        await SecureStore.deleteItemAsync('access_token');
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (token: string, refreshToken: string, userData: User) => {
    await SecureStore.setItemAsync('access_token', token);
    await SecureStore.setItemAsync('refresh_token', refreshToken);
    await AsyncStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  const logout = async () => {
    await SecureStore.deleteItemAsync('access_token');
    await SecureStore.deleteItemAsync('refresh_token');
    await AsyncStorage.removeItem('user');
    setUser(null);
  };

  const refreshUser = async () => {
    try {
      const response = await api.get('/auth/profile/details/');
      const userData = response.data.data;
      const alignedUser = {
        ...userData,
        organization: userData.organization_details,
      };
      setUser(alignedUser);
      await AsyncStorage.setItem('user', JSON.stringify(alignedUser));
    } catch {
      // silently fail
    }
  };

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated: !!user, isLoading, login, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}

export function useOrgAdmin(): boolean {
  const { user } = useAuth();
  return user?.organization?.is_owner || user?.organization?.is_admin || false;
}

export function usePlatformAdmin(): boolean {
  const { user } = useAuth();
  return user?.is_platform_admin ?? false;
}
