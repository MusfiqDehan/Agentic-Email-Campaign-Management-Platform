'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import Cookies from 'js-cookie';
import api from '@/lib/axios';
import { useRouter } from 'next/navigation';

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  organization?: {
    id: string;
    name: string;
  };
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, refreshToken: string, user: User) => void;
  logout: () => void;
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

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, logout }}>
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
