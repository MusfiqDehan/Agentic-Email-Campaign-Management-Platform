import api from '@/config/axios';

export interface Notification {
  id: string;
  organization: string;
  user?: string;
  notification_type: string;
  title: string;
  message: string;
  related_object_type: string;
  related_object_id: string;
  metadata: Record<string, any>;
  is_read: boolean;
  read_at?: string;
  created_at: string;
  updated_at: string;
}

export const fetchNotifications = async (): Promise<Notification[]> => {
  const response = await api.get('/campaigns/notifications/');
  const data = response.data.data || response.data;
  return Array.isArray(data) ? data : [];
};

export const fetchUnreadCount = async (): Promise<number> => {
  const response = await api.get('/campaigns/notifications/unread-count/');
  const data = response.data.data || response.data;
  return typeof data.count === 'number' ? data.count : 0;
};

export const markNotificationAsRead = async (notificationId: string): Promise<void> => {
  await api.post(`/campaigns/notifications/${notificationId}/mark-read/`);
};

export const markAllNotificationsAsRead = async (): Promise<number> => {
  const response = await api.post('/campaigns/notifications/mark-all-read/');
  const data = response.data.data || response.data;
  return data.updated_count;
};

export const deleteNotification = async (notificationId: string): Promise<void> => {
  await api.delete(`/campaigns/notifications/${notificationId}/`);
};
