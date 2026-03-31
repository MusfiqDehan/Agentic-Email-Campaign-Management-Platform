import api from '@/config/axios';

export interface Template {
  id: string;
  template_name: string;
  email_subject: string;
  email_body?: string;
  preview_text?: string;
  description?: string;
  category: string;
  is_global: boolean;
  version?: number;
  usage_count?: number;
  created_at: string;
  updated_at?: string;
}

export const fetchTemplates = async (): Promise<Template[]> => {
  const response = await api.get('/campaigns/templates/');
  const data = response.data;
  return Array.isArray(data) ? data : data.data || [];
};

export const fetchTemplateById = async (templateId: string): Promise<Template> => {
  const response = await api.get(`/campaigns/templates/${templateId}/`);
  return response.data.data || response.data;
};

export const createTemplate = async (payload: Partial<Template>): Promise<Template> => {
  const response = await api.post('/campaigns/templates/', payload);
  return response.data.data || response.data;
};

export const updateTemplate = async (
  templateId: string,
  payload: Partial<Template>
): Promise<Template> => {
  const response = await api.patch(`/campaigns/templates/${templateId}/`, payload);
  return response.data.data || response.data;
};

export const deleteTemplate = async (templateId: string): Promise<void> => {
  await api.delete(`/campaigns/templates/${templateId}/`);
};

export const duplicateTemplate = async (templateId: string): Promise<Template> => {
  const response = await api.post(`/campaigns/templates/${templateId}/duplicate/`);
  return response.data.data || response.data;
};
