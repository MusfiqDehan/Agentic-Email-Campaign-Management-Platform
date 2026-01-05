import axios from '@/config/axios';

export interface Campaign {
  id: string;
  name: string;
  status: string;
  stats_sent: number;
  stats_delivered: number;
  stats_opened: number;
  stats_clicked: number;
  stats_total_recipients: number;
  updated_at: string;
  [key: string]: any;
}

export interface CampaignsListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Campaign[];
}

// Fetch all campaigns with pagination
export const fetchCampaigns = async (page?: number, search?: string): Promise<CampaignsListResponse> => {
  const params: Record<string, any> = {};
  if (page) params.page = page;
  if (search) params.search = search;

  const response = await axios.get('/campaigns/campaigns/', { params });
  return response.data;
};

// Fetch a single campaign by ID
export const fetchCampaignById = async (campaignId: string): Promise<Campaign> => {
  const response = await axios.get(`/campaigns/campaigns/${campaignId}/`);
  return response.data;
};

// Update campaign status
export const updateCampaignStatus = async (campaignId: string, status: string): Promise<Campaign> => {
  const response = await axios.patch(`/campaigns/campaigns/${campaignId}/`, {
    status
  });
  return response.data;
};

// Send campaign
export const sendCampaign = async (campaignId: string): Promise<Campaign> => {
  const response = await axios.post(`/campaigns/campaigns/${campaignId}/send/`);
  return response.data;
};

// Pause campaign
export const pauseCampaign = async (campaignId: string): Promise<Campaign> => {
  const response = await axios.post(`/campaigns/campaigns/${campaignId}/pause/`);
  return response.data;
};

// Resume campaign
export const resumeCampaign = async (campaignId: string): Promise<Campaign> => {
  const response = await axios.post(`/campaigns/campaigns/${campaignId}/resume/`);
  return response.data;
};
