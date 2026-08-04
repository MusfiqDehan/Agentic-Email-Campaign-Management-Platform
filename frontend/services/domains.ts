import axios from '@/config/axios';

export interface DnsRecord {
  type: string;
  name: string;
  value: string;
  purpose: string;
}

export interface SendingDomain {
  id: string;
  domain: string;
  ownership_mode: 'PLATFORM' | 'ORG';
  region: string;
  status: 'PENDING_DNS' | 'PENDING_VERIFICATION' | 'VERIFIED' | 'FAILED' | 'SUSPENDED' | 'DISABLED';
  dns_records: DnsRecord[];
  mail_from_subdomain: string;
  mail_from_status: string;
  verified_at: string | null;
  last_checked_at: string | null;
  verification_error: string;
  suspension_reason: string;
  legacy: boolean;
  is_usable: boolean;
  sender_email_count: number;
  created_at: string;
  updated_at: string;
}

export interface DomainLimits {
  max_domains: number | null;
  used: number;
  feature_enabled: boolean;
  custom_domain_allowed: boolean;
  org_owned_ses_allowed: boolean;
}

export interface DomainListResponse {
  domains: SendingDomain[];
  limits: DomainLimits;
}

export const fetchDomains = async (): Promise<DomainListResponse> => {
  const response = await axios.get('/campaigns/domains/');
  return response.data.data;
};

export const registerDomain = async (payload: {
  domain: string;
  ownership_mode?: 'PLATFORM' | 'ORG';
  provider_id?: string | null;
  mail_from_subdomain?: string;
}): Promise<SendingDomain> => {
  const response = await axios.post('/campaigns/domains/', payload);
  return response.data.data;
};

export const fetchDomain = async (domainId: string): Promise<SendingDomain> => {
  const response = await axios.get(`/campaigns/domains/${domainId}/`);
  return response.data.data;
};

export const deleteDomain = async (domainId: string): Promise<void> => {
  await axios.delete(`/campaigns/domains/${domainId}/`);
};

export const fetchDomainDnsRecords = async (
  domainId: string
): Promise<{ domain: string; status: string; dns_records: DnsRecord[] }> => {
  const response = await axios.get(`/campaigns/domains/${domainId}/dns-records/`);
  return response.data.data;
};

export const verifyDomainNow = async (
  domainId: string
): Promise<{ domain: SendingDomain; verified: boolean; detail: Record<string, unknown> }> => {
  const response = await axios.post(`/campaigns/domains/${domainId}/verify/`);
  return response.data.data;
};
