import api from '@/config/axios';

export interface ContactList {
  id: string;
  name: string;
  description?: string;
  total_contacts: number;
  active_contacts: number;
  created_at: string;
}

export interface Contact {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  status: string;
  created_at: string;
}

export const fetchContactLists = async (): Promise<ContactList[]> => {
  const response = await api.get('/campaigns/contact-lists/');
  const data = response.data;
  return Array.isArray(data) ? data : data.data || [];
};

export const fetchContactListById = async (listId: string): Promise<ContactList> => {
  const response = await api.get(`/campaigns/contact-lists/${listId}/`);
  return response.data.data || response.data;
};

export const fetchContactsByList = async (listId: string): Promise<Contact[]> => {
  const response = await api.get(`/campaigns/contact-lists/${listId}/contacts/`);
  const data = response.data;
  return Array.isArray(data) ? data : data.data || [];
};

export const createContactList = async (payload: {
  name: string;
  description?: string;
}): Promise<ContactList> => {
  const response = await api.post('/campaigns/contact-lists/', payload);
  return response.data.data || response.data;
};

export const updateContactList = async (
  listId: string,
  payload: { name?: string; description?: string }
): Promise<ContactList> => {
  const response = await api.patch(`/campaigns/contact-lists/${listId}/`, payload);
  return response.data.data || response.data;
};

export const deleteContactList = async (listId: string): Promise<void> => {
  await api.delete(`/campaigns/contact-lists/${listId}/`);
};
