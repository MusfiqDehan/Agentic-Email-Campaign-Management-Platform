'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Bell, BellOff, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { usePushNotifications } from '@/hooks/usePushNotifications';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';

export default function NotificationSettings() {
  const { 
    isSupported, 
    permission, 
    subscription, 
    isLoading,
    subscribeToPush, 
    unsubscribeFromPush,
    testNotification 
  } = usePushNotifications();
  
  const [isTesting, setIsTesting] = useState(false);

  const handleEnable = async () => {
    try {
      await subscribeToPush();
      toast.success('Push notifications enabled!', {
        description: 'You will now receive notifications even when the app is closed'
      });
    } catch (error: any) {
      console.error('Failed to enable push notifications:', error);
      toast.error('Failed to enable push notifications', {
        description: error.message || 'Please try again'
      });
    }
  };

  const handleDisable = async () => {
    try {
      await unsubscribeFromPush();
      toast.success('Push notifications disabled');
    } catch (error: any) {
      console.error('Failed to disable push notifications:', error);
      toast.error('Failed to disable push notifications', {
        description: error.message || 'Please try again'
      });
    }
  };

  const handleTest = async () => {
    setIsTesting(true);
    try {
      await testNotification();
      toast.success('Test notification sent!', {
        description: 'Check your notifications'
      });
    } catch (error: any) {
      console.error('Failed to send test notification:', error);
      toast.error('Failed to send test notification', {
        description: error.message || 'Please try again'
      });
    } finally {
      setIsTesting(false);
    }
  };

  if (!isSupported) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-orange-500" />
            <CardTitle>Push Notifications</CardTitle>
          </div>
          <CardDescription>
            Push notifications are not supported in this browser
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Try using a modern browser like Chrome, Firefox, or Edge for the best experience.
          </p>
        </CardContent>
      </Card>
    );
  }

  const getPermissionBadge = () => {
    switch (permission) {
      case 'granted':
        return <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">Granted</Badge>;
      case 'denied':
        return <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">Denied</Badge>;
      default:
        return <Badge variant="outline" className="bg-gray-50 text-gray-700 border-gray-200">Not Set</Badge>;
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Push Notifications
            </CardTitle>
            <CardDescription className="mt-1">
              Get notified about campaign updates even when the app is closed
            </CardDescription>
          </div>
          {getPermissionBadge()}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Status */}
        <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
          <div className="flex items-center gap-3">
            {subscription ? (
              <>
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
                  <CheckCircle2 className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm font-medium">Push notifications enabled</p>
                  <p className="text-xs text-muted-foreground">You'll receive notifications for campaign updates</p>
                </div>
              </>
            ) : (
              <>
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-100">
                  <BellOff className="h-5 w-5 text-gray-600" />
                </div>
                <div>
                  <p className="text-sm font-medium">Push notifications disabled</p>
                  <p className="text-xs text-muted-foreground">Enable to receive notifications</p>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          {subscription ? (
            <>
              <Button 
                variant="outline" 
                onClick={handleDisable}
                disabled={isLoading}
              >
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Disable
              </Button>
              <Button 
                variant="outline" 
                onClick={handleTest}
                disabled={isTesting}
              >
                {isTesting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Send Test
              </Button>
            </>
          ) : (
            <Button 
              onClick={handleEnable}
              disabled={isLoading || permission === 'denied'}
              className="w-full sm:w-auto"
            >
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              <Bell className="mr-2 h-4 w-4" />
              Enable Push Notifications
            </Button>
          )}
        </div>

        {/* Permission denied message */}
        {permission === 'denied' && (
          <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="h-4 w-4 text-red-600 mt-0.5" />
            <div className="text-sm text-red-700">
              <p className="font-medium">Notifications blocked</p>
              <p className="text-xs mt-1">
                You've blocked notifications for this site. To enable them, click the lock icon in your browser's address bar and allow notifications.
              </p>
            </div>
          </div>
        )}

        {/* Features */}
        <div className="pt-4 border-t space-y-2">
          <p className="text-sm font-medium">What you'll get:</p>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li className="flex items-center gap-2">
              <div className="h-1.5 w-1.5 rounded-full bg-primary" />
              Real-time campaign status updates
            </li>
            <li className="flex items-center gap-2">
              <div className="h-1.5 w-1.5 rounded-full bg-primary" />
              Notifications even when browser is closed
            </li>
            <li className="flex items-center gap-2">
              <div className="h-1.5 w-1.5 rounded-full bg-primary" />
              Click to open campaign details
            </li>
            <li className="flex items-center gap-2">
              <div className="h-1.5 w-1.5 rounded-full bg-primary" />
              Works on desktop and mobile
            </li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
