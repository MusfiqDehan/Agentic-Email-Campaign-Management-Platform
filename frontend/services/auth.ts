import api from '@/config/axios';

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

export interface LoginPayload {
  email: string;
  password: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    is_platform_admin?: boolean;
    organization?: {
      id: string;
      name: string;
      slug: string;
      is_owner?: boolean;
      is_admin?: boolean;
    };
  };
  organization?: {
    id: string;
    name: string;
    slug: string;
    is_owner?: boolean;
    is_admin?: boolean;
  };
}

/**
 * Request a password reset email
 */
export const requestPasswordReset = async (payload: RequestPasswordResetPayload) => {
  const response = await api.post('/auth/request-password-reset/', payload);
  return response.data;
};

/**
 * Reset password using a token from email
 */
export const resetPassword = async (payload: ResetPasswordPayload) => {
  const response = await api.post('/auth/reset-password/', payload);
  return response.data;
};

/**
 * Change password for authenticated user
 */
export const changePassword = async (payload: ChangePasswordPayload) => {
  const response = await api.post('/auth/change-password/', payload);
  return response.data;
};

/**
 * Re-authenticate user with email and new password to get fresh tokens
 */
export const reauthenticate = async (email: string, password: string): Promise<AuthResponse> => {
  const response = await api.post('/auth/login/', { email, password });
  return response.data.data;
};
