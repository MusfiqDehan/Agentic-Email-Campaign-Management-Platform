import axios from '@/config/axios';
import type { SendingDomain } from './domains';
import type { SenderEmail } from './sender-emails';

export interface Package {
  id: string;
  name: string;
  display_name: string;
  description: string;
  is_default: boolean;
  is_active: boolean;
  sort_order: number;
  contacts_limit: number | null;
  campaigns_per_month: number | null;
  emails_per_day: number | null;
  emails_per_month: number | null;
  emails_per_minute: number | null;
  batch_size: number | null;
  api_requests_per_minute: number | null;
  max_domains: number | null;
  max_sender_emails: number | null;
  custom_domain_allowed: boolean;
  advanced_analytics: boolean;
  priority_support: boolean;
  bulk_email_allowed: boolean;
  ab_testing_allowed: boolean;
  org_owned_ses_allowed: boolean;
  organization_count?: number;
}

export type PackageInput = Partial<Omit<Package, 'id' | 'organization_count'>> & {
  name: string;
  display_name: string;
};

// ─── Packages ────────────────────────────────────────────────────────────

export const fetchPackages = async (): Promise<Package[]> => {
  const response = await axios.get('/campaigns/admin/packages/');
  return response.data.data;
};

export const createPackage = async (payload: PackageInput): Promise<Package> => {
  const response = await axios.post('/campaigns/admin/packages/', payload);
  return response.data.data;
};

export const updatePackage = async (packageId: string, payload: Partial<PackageInput>): Promise<Package> => {
  const response = await axios.patch(`/campaigns/admin/packages/${packageId}/`, payload);
  return response.data.data;
};

export const deletePackage = async (packageId: string): Promise<void> => {
  await axios.delete(`/campaigns/admin/packages/${packageId}/`);
};

// ─── Per-organization control ────────────────────────────────────────────

export const assignPackage = async (organizationId: string, packageId: string) => {
  const response = await axios.post(
    `/campaigns/admin/organizations/${organizationId}/assign-package/`,
    { package_id: packageId }
  );
  return response.data.data;
};

export const fetchLimitOverrides = async (organizationId: string) => {
  const response = await axios.get(`/campaigns/admin/organizations/${organizationId}/limit-overrides/`);
  return response.data.data;
};

export const updateLimitOverrides = async (
  organizationId: string,
  overrides: Record<string, number | boolean | null>
) => {
  const response = await axios.patch(
    `/campaigns/admin/organizations/${organizationId}/limit-overrides/`,
    overrides
  );
  return response.data.data;
};

export const setDomainFeature = async (organizationId: string, enabled: boolean) => {
  const response = await axios.post(
    `/campaigns/admin/organizations/${organizationId}/domain-feature/`,
    { enabled }
  );
  return response.data;
};

export const fetchDomainUsage = async (organizationId: string) => {
  const response = await axios.get(`/campaigns/admin/organizations/${organizationId}/domain-usage/`);
  return response.data.data;
};

// ─── Cross-tenant domain / sender-email control ──────────────────────────

export const fetchAllDomains = async (filters?: {
  organization?: string;
  status?: string;
}): Promise<SendingDomain[]> => {
  const response = await axios.get('/campaigns/admin/domains/', { params: filters });
  return response.data.data;
};

export const suspendDomain = async (domainId: string, reason?: string) => {
  const response = await axios.post(`/campaigns/admin/domains/${domainId}/suspend/`, { reason });
  return response.data.data;
};

export const reactivateDomain = async (domainId: string) => {
  const response = await axios.post(`/campaigns/admin/domains/${domainId}/reactivate/`);
  return response.data.data;
};

export const suspendSenderEmail = async (senderEmailId: string, reason?: string) => {
  const response = await axios.post(`/campaigns/admin/sender-emails/${senderEmailId}/suspend/`, { reason });
  return response.data.data;
};

export const reactivateSenderEmail = async (senderEmailId: string) => {
  const response = await axios.post(`/campaigns/admin/sender-emails/${senderEmailId}/reactivate/`);
  return response.data.data;
};

// ─── Admin-on-behalf creation ────────────────────────────────────────────

export const createDomainForOrganization = async (
  organizationId: string,
  payload: { domain: string; ownership_mode?: 'PLATFORM' | 'ORG'; provider_id?: string }
): Promise<SendingDomain> => {
  const response = await axios.post(`/campaigns/admin/organizations/${organizationId}/domains/`, payload);
  return response.data.data;
};

export const createSenderEmailForOrganization = async (
  organizationId: string,
  payload: { domain_id: string; local_part: string; display_name?: string }
): Promise<SenderEmail> => {
  const response = await axios.post(
    `/campaigns/admin/organizations/${organizationId}/sender-emails/`,
    payload
  );
  return response.data.data;
};
