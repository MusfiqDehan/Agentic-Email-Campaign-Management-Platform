import api from './api';
import { Campaign, Contact, ContactList, EmailTemplate, CampaignStats } from '@/types';

// Campaign API
export const campaignApi = {
  getAll: () => api.get<{ results: Campaign[] }>('/api/campaigns/'),
  getOne: (id: number) => api.get<Campaign>(`/api/campaigns/${id}/`),
  create: (data: Partial<Campaign>) => api.post<Campaign>('/api/campaigns/', data),
  update: (id: number, data: Partial<Campaign>) => api.patch<Campaign>(`/api/campaigns/${id}/`, data),
  delete: (id: number) => api.delete(`/api/campaigns/${id}/`),
  addContacts: (id: number, contactIds: number[]) => 
    api.post(`/api/campaigns/${id}/add_contacts/`, { contact_ids: contactIds }),
  send: (id: number) => api.post(`/api/campaigns/${id}/send/`),
  getStats: (id: number) => api.get<CampaignStats>(`/api/campaigns/${id}/stats/`),
};

// Contact API
export const contactApi = {
  getAll: (params?: { list_id?: number; is_active?: boolean }) => 
    api.get<{ results: Contact[] }>('/api/contacts/', { params }),
  getOne: (id: number) => api.get<Contact>(`/api/contacts/${id}/`),
  create: (data: Partial<Contact>) => api.post<Contact>('/api/contacts/', data),
  update: (id: number, data: Partial<Contact>) => api.patch<Contact>(`/api/contacts/${id}/`, data),
  delete: (id: number) => api.delete(`/api/contacts/${id}/`),
};

// Contact List API
export const contactListApi = {
  getAll: () => api.get<{ results: ContactList[] }>('/api/contacts/lists/'),
  getOne: (id: number) => api.get<ContactList>(`/api/contacts/lists/${id}/`),
  create: (data: Partial<ContactList>) => api.post<ContactList>('/api/contacts/lists/', data),
  update: (id: number, data: Partial<ContactList>) => api.patch<ContactList>(`/api/contacts/lists/${id}/`, data),
  delete: (id: number) => api.delete(`/api/contacts/lists/${id}/`),
  getContacts: (id: number) => api.get<Contact[]>(`/api/contacts/lists/${id}/contacts/`),
};

// Email Template API
export const templateApi = {
  getAll: (params?: { is_active?: boolean }) => 
    api.get<{ results: EmailTemplate[] }>('/api/templates/', { params }),
  getOne: (id: number) => api.get<EmailTemplate>(`/api/templates/${id}/`),
  create: (data: Partial<EmailTemplate>) => api.post<EmailTemplate>('/api/templates/', data),
  update: (id: number, data: Partial<EmailTemplate>) => api.patch<EmailTemplate>(`/api/templates/${id}/`, data),
  delete: (id: number) => api.delete(`/api/templates/${id}/`),
};
