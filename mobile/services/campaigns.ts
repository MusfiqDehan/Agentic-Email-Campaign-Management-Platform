import api from '@/config/axios';

export interface Campaign {
  id: string;
  name: string;
  subject: string;
  status: string;
  stats_sent: number;
  stats_delivered: number;
  stats_opened: number;
  stats_clicked: number;
  stats_total_recipients: number;
  updated_at: string;
  created_at: string;
  [key: string]: any;
}

export interface CampaignsListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Campaign[];
}

export const fetchCampaigns = async (
  page?: number,
  search?: string
): Promise<Campaign[]> => {
  const params: Record<string, any> = {};
  if (page) params.page = page;
  if (search) params.search = search;
  const response = await api.get('/campaigns/', { params });
  const data = response.data;
  return Array.isArray(data) ? data : data.data || [];
};

export const fetchCampaignById = async (campaignId: string): Promise<Campaign> => {
  const response = await api.get(`/campaigns/campaigns/${campaignId}/`);
  return response.data;
};

export const sendCampaign = async (campaignId: string): Promise<Campaign> => {
  const response = await api.post(`/campaigns/campaigns/${campaignId}/send/`);
  return response.data;
};

export const pauseCampaign = async (campaignId: string): Promise<Campaign> => {
  const response = await api.post(`/campaigns/campaigns/${campaignId}/pause/`);
  return response.data;
};

export const resumeCampaign = async (campaignId: string): Promise<Campaign> => {
  const response = await api.post(`/campaigns/campaigns/${campaignId}/resume/`);
  return response.data;
};

export const createCampaign = async (payload: Partial<Campaign>): Promise<Campaign> => {
  const response = await api.post('/campaigns/campaigns/', payload);
  return response.data;
};

export const updateCampaign = async (
  campaignId: string,
  payload: Partial<Campaign>
): Promise<Campaign> => {
  const response = await api.patch(`/campaigns/campaigns/${campaignId}/`, payload);
  return response.data;
};

export const deleteCampaign = async (campaignId: string): Promise<void> => {
  await api.delete(`/campaigns/campaigns/${campaignId}/`);
};
