import axios from '@/config/axios';

export interface SenderEmail {
  id: string;
  domain: string;
  domain_name: string;
  local_part: string;
  email_address: string;
  display_name: string;
  status: 'ACTIVE' | 'SUSPENDED';
  suspension_reason: string;
  mailbox_account: string | null;
  receiving_supported: boolean;
  is_usable: boolean;
  created_at: string;
  updated_at: string;
}

export interface SenderEmailListResponse {
  sender_emails: SenderEmail[];
  limits: {
    max_sender_emails: number | null;
    used: number;
  };
}

export const fetchSenderEmails = async (domainId?: string): Promise<SenderEmailListResponse> => {
  const params: Record<string, string> = {};
  if (domainId) params.domain = domainId;
  const response = await axios.get('/campaigns/sender-emails/', { params });
  return response.data.data;
};

export const createSenderEmail = async (payload: {
  domain_id: string;
  local_part: string;
  display_name?: string;
}): Promise<SenderEmail> => {
  const response = await axios.post('/campaigns/sender-emails/', payload);
  return response.data.data;
};

export const updateSenderEmail = async (
  senderEmailId: string,
  payload: { display_name?: string }
): Promise<SenderEmail> => {
  const response = await axios.patch(`/campaigns/sender-emails/${senderEmailId}/`, payload);
  return response.data.data;
};

export const deleteSenderEmail = async (senderEmailId: string): Promise<void> => {
  await axios.delete(`/campaigns/sender-emails/${senderEmailId}/`);
};
