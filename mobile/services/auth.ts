import api from '@/config/axios';
import { User } from '@/contexts/AuthContext';

export interface LoginPayload {
  email: string;
  password: string;
}

export interface SignupPayload {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  organization_name: string;
  terms_accepted: boolean;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface RequestPasswordResetPayload {
  email: string;
}

export interface ResetPasswordPayload {
  token: string;
  new_password: string;
}

export interface ChangePasswordPayload {
  old_password: string;
  new_password: string;
}

export const login = async (payload: LoginPayload): Promise<AuthResponse> => {
  const response = await api.post('/auth/login/', payload);
  return response.data.data;
};

export const signup = async (payload: SignupPayload): Promise<AuthResponse | null> => {
  const response = await api.post('/auth/signup/', payload);
  return response.data.data || null;
};

export const requestPasswordReset = async (payload: RequestPasswordResetPayload) => {
  const response = await api.post('/auth/request-password-reset/', payload);
  return response.data;
};

export const resetPassword = async (payload: ResetPasswordPayload) => {
  const response = await api.post('/auth/reset-password/', payload);
  return response.data;
};

export const changePassword = async (payload: ChangePasswordPayload) => {
  const response = await api.post('/auth/change-password/', payload);
  return response.data;
};

export const reauthenticate = async (
  email: string,
  password: string
): Promise<AuthResponse> => {
  const response = await api.post('/auth/login/', { email, password });
  return response.data.data;
};
