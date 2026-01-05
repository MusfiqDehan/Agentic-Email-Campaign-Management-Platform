import { useState, useEffect, useCallback, useRef } from 'react';
import { fetchNotifications, fetchUnreadCount, markNotificationAsRead, markAllNotificationsAsRead, Notification } from '@/services/notifications';
import Cookies from 'js-cookie';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001';

export const useNotifications = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);
  const MAX_RECONNECT_ATTEMPTS = 5;
  const RECONNECT_DELAY = 3001; // 3 seconds

  // Fetch notifications
  const loadNotifications = useCallback(async () => {
    try {
      setError(null);
      const data = await fetchNotifications();
      setNotifications(data);
      // Update unread count based on notifications
      const unread = data.filter(n => !n.is_read).length;
      setUnreadCount(unread);
    } catch (err: any) {
      console.error('Failed to fetch notifications:', err);
      setError(err?.message || 'Failed to load notifications');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch unread count
  const loadUnreadCount = useCallback(async () => {
    try {
      const count = await fetchUnreadCount();
      setUnreadCount(count);
    } catch (err: any) {
      console.error('Failed to fetch unread count:', err);
      // Fallback: calculate from loaded notifications
      setUnreadCount(prev => prev);
    }
  }, []);

  // Mark a single notification as read
  const markAsRead = useCallback(async (notificationId: string) => {
    try {
      await markNotificationAsRead(notificationId);
      
      // Update local state
      setNotifications(prevNotifications =>
        prevNotifications.map(notification =>
          notification.id === notificationId
            ? { ...notification, is_read: true, read_at: new Date().toISOString() }
            : notification
        )
      );

      // Decrement unread count
      setUnreadCount(prevCount => Math.max(0, prevCount - 1));
    } catch (err: any) {
      console.error('Failed to mark notification as read:', err);
      throw err;
    }
  }, []);

  // Mark all notifications as read
  const markAllAsRead = useCallback(async () => {
    try {
      await markAllNotificationsAsRead();
      
      // Update all notifications to read
      setNotifications(prevNotifications =>
        prevNotifications.map(notification => ({
          ...notification,
          is_read: true,
          read_at: new Date().toISOString()
        }))
      );

      // Reset unread count
      setUnreadCount(0);
    } catch (err: any) {
      console.error('Failed to mark all notifications as read:', err);
      throw err;
    }
  }, []);

  // Refresh all notification data
  const refresh = useCallback(async () => {
    await Promise.all([loadNotifications(), loadUnreadCount()]);
  }, [loadNotifications, loadUnreadCount]);

  // WebSocket connection management
  const connectWebSocket = useCallback(() => {
    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
    }

    try {
      // Get auth token from cookies
      const accessToken = Cookies.get('access_token');
      if (!accessToken) {
        console.error('No access token found, cannot connect to WebSocket');
        return;
      }

      // Create WebSocket connection with auth token
      const ws = new WebSocket(`${WS_URL}/ws/notifications/?token=${accessToken}`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('WebSocket message received:', message);

          if (message.type === 'notification') {
            // New notification received - add to list
            setNotifications(prev => [message.data, ...prev]);
            
            // Update unread count if notification is unread
            if (!message.data.is_read) {
              setUnreadCount(prev => prev + 1);
            }
          } else if (message.type === 'unread_count') {
            // Unread count update
            setUnreadCount(message.count);
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection error');
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected', event.code, event.reason);
        setIsConnected(false);

        // Attempt to reconnect if not a manual close
        if (event.code !== 1000 && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttemptsRef.current += 1;
          console.log(`Reconnecting... Attempt ${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS}`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, RECONNECT_DELAY);
        } else if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
          setError('Failed to connect to notification service. Please refresh the page.');
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to create WebSocket connection:', err);
      setError('Failed to establish real-time connection');
    }
  }, []);

  // Initial load and WebSocket setup
  useEffect(() => {
    console.log('useNotifications: Initializing...');
    
    // Initial load of notifications
    const initialLoad = async () => {
      await Promise.all([loadNotifications(), loadUnreadCount()]);
    };
    initialLoad();

    // Connect to WebSocket for real-time updates
    connectWebSocket();

    // Cleanup on unmount
    return () => {
      console.log('useNotifications: Cleaning up...');
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      if (wsRef.current) {
        wsRef.current.close(1000); // Normal closure
        wsRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array - only run once on mount

  return {
    notifications,
    unreadCount,
    loading,
    error,
    isConnected,
    markAsRead,
    markAllAsRead,
    refresh
  };
};
