export interface Campaign {
  id: number;
  name: string;
  subject: string;
  from_email: string;
  from_name: string;
  template: number | null;
  status: 'draft' | 'scheduled' | 'sent' | 'failed';
  scheduled_at: string | null;
  sent_at: string | null;
  created_at: string;
  updated_at: string;
  total_contacts?: number;
  sent_count?: number;
  opened_count?: number;
  clicked_count?: number;
}

export interface Contact {
  id: number;
  email: string;
  name: string;
  first_name: string;
  last_name: string;
  company: string;
  phone: string;
  lists: number[];
  lists_data?: ContactList[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ContactList {
  id: number;
  name: string;
  description: string;
  contact_count?: number;
  created_at: string;
  updated_at: string;
}

export interface EmailTemplate {
  id: number;
  name: string;
  description: string;
  subject: string;
  html_content: string;
  text_content: string;
  variables: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CampaignStats {
  total_contacts: number;
  sent: number;
  opened: number;
  clicked: number;
  bounced: number;
}
