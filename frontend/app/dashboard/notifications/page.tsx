'use client';

import { useEffect, useState } from 'react';
import api from '@/config/axios';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Bell, Check, CheckCheck, Filter, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { formatRelativeTime } from '@/lib/template-utils';
import { NOTIFICATION_TYPES } from '@/config/constants';

interface Notification {
  id: string;
  notification_type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
  template?: {
    id: string;
    name: string;
  };
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  const fetchNotifications = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/campaigns/organization/template-notifications/');
      setNotifications(response.data.data || []);
    } catch (error) {
      console.error(error);
      toast.error('Failed to fetch notifications');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const markAsRead = async (id: string) => {
    try {
      await api.post(`/campaigns/organization/template-notifications/${id}/mark-read/`);
      setNotifications(notifications.map(n => 
        n.id === id ? { ...n, is_read: true } : n
      ));
      toast.success('Notification marked as read');
    } catch {
      toast.error('Failed to mark as read');
    }
  };

  const markAllAsRead = async () => {
    try {
      const unreadIds = notifications.filter(n => !n.is_read).map(n => n.id);
      await Promise.all(
        unreadIds.map(id => 
          api.post(`/campaigns/organization/template-notifications/${id}/mark-read/`)
        )
      );
      setNotifications(notifications.map(n => ({ ...n, is_read: true })));
      toast.success('All notifications marked as read');
    } catch {
      toast.error('Failed to mark all as read');
    }
  };

  const filteredNotifications = filter === 'all' 
    ? notifications 
    : notifications.filter(n => !n.is_read);

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Notifications</h1>
          <p className="text-muted-foreground">
            Stay updated with template changes and approvals
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setFilter(filter === 'all' ? 'unread' : 'all')}
          >
            <Filter className="h-4 w-4 mr-2" />
            {filter === 'all' ? 'Show Unread Only' : 'Show All'}
          </Button>
          {unreadCount > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={markAllAsRead}
            >
              <CheckCheck className="h-4 w-4 mr-2" />
              Mark All Read
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={fetchNotifications}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {unreadCount > 0 && (
        <Card className="border-primary/50 bg-primary/5">
          <CardContent className="p-4">
            <p className="text-sm font-medium">
              You have {unreadCount} unread notification{unreadCount !== 1 ? 's' : ''}
            </p>
          </CardContent>
        </Card>
      )}

      <div className="space-y-3">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto" />
            <p className="mt-4 text-muted-foreground">Loading notifications...</p>
          </div>
        ) : filteredNotifications.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <Bell className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">
                {filter === 'unread' ? 'No unread notifications' : 'No notifications yet'}
              </h3>
              <p className="text-muted-foreground">
                {filter === 'unread' 
                  ? 'You\'re all caught up!' 
                  : 'When template updates or approvals happen, you\'ll see them here'
                }
              </p>
            </CardContent>
          </Card>
        ) : (
          filteredNotifications.map((notification) => (
            <Card 
              key={notification.id}
              className={notification.is_read ? 'opacity-60' : 'border-primary/30'}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-2xl">
                        {NOTIFICATION_TYPES.TEMPLATE_UPDATE.icon}
                      </span>
                      <h3 className="font-semibold">{notification.title}</h3>
                      {!notification.is_read && (
                        <Badge variant="secondary" className="ml-2">New</Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">
                      {notification.message}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatRelativeTime(notification.created_at)}
                    </p>
                  </div>
                  {!notification.is_read && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => markAsRead(notification.id)}
                    >
                      <Check className="h-4 w-4 mr-2" />
                      Mark Read
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
