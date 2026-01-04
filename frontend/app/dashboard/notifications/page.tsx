'use client';

import { useState } from 'react';
import { useNotifications } from '@/hooks/useNotifications';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Mail, UserPlus, AlertCircle, CheckCheck, Trash2, Loader2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { deleteNotification } from '@/services/notifications';
import { toast } from 'sonner';

export default function NotificationsPage() {
  const { notifications, unreadCount, markAsRead, markAllAsRead, refresh } = useNotifications();
  const [activeTab, setActiveTab] = useState('all');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Get notification icon based on type
  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'CAMPAIGN_SENT':
        return <Mail className="h-5 w-5 text-blue-500" />;
      case 'CONTACT_ADDED':
        return <UserPlus className="h-5 w-5 text-green-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-orange-500" />;
    }
  };

  // Get notification icon background based on type
  const getNotificationIconBg = (type: string) => {
    switch (type) {
      case 'CAMPAIGN_SENT':
        return 'bg-blue-500/10';
      case 'CONTACT_ADDED':
        return 'bg-green-500/10';
      default:
        return 'bg-orange-500/10';
    }
  };

  // Filter notifications based on active tab
  const filteredNotifications = notifications.filter(notification => {
    if (activeTab === 'unread') return !notification.is_read;
    if (activeTab === 'read') return notification.is_read;
    return true;
  });

  // Handle marking notification as read
  const handleMarkAsRead = async (notificationId: string, isRead: boolean) => {
    if (!isRead) {
      try {
        await markAsRead(notificationId);
        toast.success('Notification marked as read');
      } catch (error) {
        toast.error('Failed to mark notification as read');
      }
    }
  };

  // Handle marking all as read
  const handleMarkAllAsRead = async () => {
    try {
      await markAllAsRead();
      toast.success('All notifications marked as read');
    } catch (error) {
      toast.error('Failed to mark all as read');
    }
  };

  // Handle deleting notification
  const handleDelete = async (notificationId: string) => {
    setDeletingId(notificationId);
    try {
      await deleteNotification(notificationId);
      await refresh(); // Refresh the notification list
      toast.success('Notification deleted');
    } catch (error) {
      toast.error('Failed to delete notification');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Notifications</h1>
          <p className="text-muted-foreground mt-1">
            Stay updated with your campaign activities
          </p>
        </div>
        {unreadCount > 0 && (
          <Button onClick={handleMarkAllAsRead} variant="outline" size="sm">
            <CheckCheck className="h-4 w-4 mr-2" />
            Mark all as read
          </Button>
        )}
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-3">
          <TabsTrigger value="all">
            All ({notifications.length})
          </TabsTrigger>
          <TabsTrigger value="unread">
            Unread ({unreadCount})
          </TabsTrigger>
          <TabsTrigger value="read">
            Read ({notifications.length - unreadCount})
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-6">
          {filteredNotifications.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <div className="rounded-full bg-muted p-4 mb-4">
                  <Mail className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="text-lg font-semibold mb-1">No notifications</h3>
                <p className="text-sm text-muted-foreground">
                  {activeTab === 'unread' 
                    ? "You're all caught up!"
                    : activeTab === 'read'
                    ? 'No read notifications yet'
                    : 'You have no notifications yet'}
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {filteredNotifications.map((notification) => (
                <Card 
                  key={notification.id} 
                  className={`transition-all hover:shadow-md ${
                    !notification.is_read ? 'border-l-4 border-l-primary' : ''
                  }`}
                >
                  <CardContent className="p-4">
                    <div className="flex gap-4">
                      {/* Icon */}
                      <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full ${getNotificationIconBg(notification.notification_type)}`}>
                        {getNotificationIcon(notification.notification_type)}
                      </div>

                      {/* Content */}
                      <div className="flex-1 space-y-1">
                        <div className="flex items-start justify-between gap-2">
                          <h3 className="font-semibold text-base">
                            {notification.title}
                          </h3>
                          {!notification.is_read && (
                            <div className="flex h-2 w-2 shrink-0 items-center justify-center rounded-full bg-primary mt-1.5" />
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {notification.message}
                        </p>
                        
                        {/* Metadata */}
                        {notification.metadata && Object.keys(notification.metadata).length > 0 && (
                          <div className="flex flex-wrap gap-2 mt-2">
                            {notification.metadata.campaign_name && (
                              <span className="inline-flex items-center rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium">
                                {notification.metadata.campaign_name}
                              </span>
                            )}
                            {notification.metadata.total_sent && (
                              <span className="inline-flex items-center rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium">
                                {notification.metadata.total_sent} sent
                              </span>
                            )}
                          </div>
                        )}

                        {/* Actions */}
                        <div className="flex items-center gap-4 mt-3">
                          <span className="text-xs text-muted-foreground">
                            {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                          </span>
                          <div className="flex gap-2">
                            {!notification.is_read && (
                              <Button 
                                onClick={() => handleMarkAsRead(notification.id, notification.is_read)}
                                variant="ghost" 
                                size="sm"
                                className="h-7 text-xs"
                              >
                                Mark as read
                              </Button>
                            )}
                            <Button 
                              onClick={() => handleDelete(notification.id)}
                              variant="ghost" 
                              size="sm"
                              className="h-7 text-xs text-destructive hover:text-destructive"
                              disabled={deletingId === notification.id}
                            >
                              {deletingId === notification.id ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              ) : (
                                <Trash2 className="h-3 w-3" />
                              )}
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
