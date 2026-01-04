'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import Cookies from 'js-cookie';
import api from '@/config/axios';
import { useRouter } from 'next/navigation';

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  profile_picture?: string;
  is_org_admin?: boolean;
  is_platform_admin?: boolean;
  organization?: {
    id: string;
    name: string;
    is_owner?: boolean;
    is_admin?: boolean;
  };
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, refreshToken: string, user: User) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const initializeAuth = async () => {
      const token = Cookies.get('access_token');
      if (token) {
        try {
          // Ideally, we should have a /me endpoint to fetch user details
          // For now, we'll assume if token exists, we might have user data in localStorage or fetch it
          // Let's try to fetch user profile if endpoint exists, otherwise rely on stored user
          const storedUser = localStorage.getItem('user');
          if (storedUser) {
            setUser(JSON.parse(storedUser));
          }
        } catch (error) {
          console.error('Auth initialization failed', error);
          Cookies.remove('access_token');
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = (token: string, refreshToken: string, userData: User) => {
    Cookies.set('access_token', token, { expires: 1 }); // 1 day
    Cookies.set('refresh_token', refreshToken, { expires: 7 }); // 7 days
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
    router.push('/dashboard');
  };

  const logout = () => {
    Cookies.remove('access_token');
    Cookies.remove('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
    router.push('/login');
  };

  const refreshUser = async () => {
    try {
      const response = await api.get('/auth/profile/details/');
      const userData = response.data.data;

      // Ensure organization details are mapped correctly for consistent usage
      const alignedUser = {
        ...userData,
        organization: userData.organization_details
      };

      console.log('Refreshing user data:', alignedUser);

      // Update local state and storage
      setUser(alignedUser);
      localStorage.setItem('user', JSON.stringify(alignedUser));
    } catch (error) {
      console.error('Failed to refresh user data:', error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

/**
 * Hook to check if the current user is a platform administrator.
 * @returns boolean indicating if user has platform admin privileges
 */
export function usePlatformAdmin(): boolean {
  const { user } = useAuth();
  return user?.is_platform_admin ?? false;
}

/**
 * Hook to check if the current user is an organization administrator.
 * @returns boolean indicating if user is owner or admin of their organization
 */
export function useOrgAdmin(): boolean {
  const { user } = useAuth();
  return user?.organization?.is_owner || user?.organization?.is_admin || false;
}
