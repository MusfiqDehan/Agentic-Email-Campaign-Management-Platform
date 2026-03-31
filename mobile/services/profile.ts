import api from '@/config/axios';

export interface ProfileData {
  first_name: string;
  last_name: string;
  email: string;
  phone_number?: string;
  occupation?: string;
  country?: string;
  city?: string;
  address?: string;
  profile_picture?: string;
  organization_details?: {
    name?: string;
    description?: string;
    logo?: string;
    slug?: string;
  };
}

export interface DashboardStats {
  total_campaigns?: number;
  total_contacts?: number;
  emails_sent?: number;
  open_rate?: number;
  recent_campaigns?: Array<{
    id: string;
    name: string;
    created_at: string;
    status: string;
  }>;
  recent_activity?: Array<{
    id: string;
    recipient: string;
    campaign_name: string;
    status: string;
    sent_at: string;
  }>;
}

export const fetchProfile = async (): Promise<ProfileData> => {
  const response = await api.get('/auth/profile/details/');
  return response.data.data;
};

export const updateProfile = async (formData: FormData): Promise<ProfileData> => {
  const response = await api.patch('/auth/profile/update/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data.data;
};

export const fetchDashboardStats = async (): Promise<DashboardStats> => {
  const response = await api.get('/campaigns/org/stats/');
  return response.data;
};

export interface TeamStats {
  total_members: number;
  total_templates_used: number;
  most_used_template: { name: string; usage_count: number };
  active_members_count: number;
}

export interface TemplateUsage {
  id: string;
  user: { id: string; name: string; email: string };
  template: { id: string; name: string; category: string };
  action: string;
  created_at: string;
}

export const fetchTeamStats = async (): Promise<TeamStats | null> => {
  const response = await api.get('/campaigns/organization/team-template-stats/');
  return response.data.data || null;
};

export const fetchTemplateUsageLogs = async (): Promise<TemplateUsage[]> => {
  const response = await api.get('/campaigns/organization/template-usage/');
  return response.data.data || [];
};
