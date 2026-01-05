import { useState, useEffect } from 'react';
import axios from '@/config/axios';

const PUBLIC_VAPID_KEY = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || '';

export interface PushSubscriptionState {
  isSupported: boolean;
  permission: NotificationPermission;
  subscription: PushSubscription | null;
  isLoading: boolean;
}

export const usePushNotifications = () => {
  const [isSupported, setIsSupported] = useState(false);
  const [subscription, setSubscription] = useState<PushSubscription | null>(null);
  const [permission, setPermission] = useState<NotificationPermission>('default');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Check if push notifications are supported
    const supported = 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
    setIsSupported(supported);
    
    if (supported) {
      setPermission(Notification.permission);
      checkExistingSubscription();
    }
  }, []);

  const checkExistingSubscription = async () => {
    try {
      const registration = await navigator.serviceWorker.ready;
      const existingSub = await registration.pushManager.getSubscription();
      setSubscription(existingSub);
    } catch (error) {
      console.error('Error checking existing subscription:', error);
    }
  };

  const registerServiceWorker = async () => {
    if (!isSupported) {
      throw new Error('Push notifications not supported');
    }
    
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/'
      });
      
      console.log('Service Worker registered:', registration);
      
      // Wait for service worker to be ready
      await navigator.serviceWorker.ready;
      
      return registration;
    } catch (error) {
      console.error('Service Worker registration failed:', error);
      throw error;
    }
  };

  const subscribeToPush = async () => {
    if (!isSupported) {
      throw new Error('Push notifications not supported in this browser');
    }

    if (!PUBLIC_VAPID_KEY) {
      throw new Error('VAPID public key not configured');
    }

    setIsLoading(true);
    
    try {
      // Register service worker
      const registration = await registerServiceWorker();
      
      // Unsubscribe any existing subscription first (in case VAPID key changed)
      const existingSub = await registration.pushManager.getSubscription();
      if (existingSub) {
        console.log('Unsubscribing existing push subscription...');
        await existingSub.unsubscribe();
      }
      
      // Request notification permission
      const permissionResult = await Notification.requestPermission();
      setPermission(permissionResult);

      if (permissionResult !== 'granted') {
        throw new Error('Notification permission denied');
      }

      // Subscribe to push notifications
      const applicationServerKey = urlBase64ToUint8Array(PUBLIC_VAPID_KEY) as Uint8Array<ArrayBuffer>;
      const sub = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey,
      });

      console.log('Push subscription created:', sub);

      // Send subscription to backend
      const response = await axios.post('/campaigns/push/subscribe/', {
        subscription: sub.toJSON()
      });
      
      console.log('Push subscription saved to backend:', response.data);

      setSubscription(sub);
      return sub;
    } catch (error) {
      console.error('Error subscribing to push notifications:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const unsubscribeFromPush = async () => {
    if (!subscription) {
      throw new Error('No active subscription');
    }

    setIsLoading(true);

    try {
      // Unsubscribe from push
      await subscription.unsubscribe();
      
      // Delete from backend
      const endpoint = encodeURIComponent(subscription.endpoint);
      await axios.delete(`/campaigns/push/unsubscribe/?endpoint=${endpoint}`);
      
      setSubscription(null);
    } catch (error) {
      console.error('Error unsubscribing from push notifications:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const testNotification = async () => {
    if (!subscription) {
      throw new Error('No active subscription');
    }

    try {
      await axios.post('/campaigns/push/test/', {
        endpoint: subscription.endpoint
      });
    } catch (error) {
      console.error('Error sending test notification:', error);
      throw error;
    }
  };

  return {
    isSupported,
    permission,
    subscription,
    isLoading,
    subscribeToPush,
    unsubscribeFromPush,
    testNotification
  };
};

// Helper function to convert VAPID key
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  
  return outputArray;
}
