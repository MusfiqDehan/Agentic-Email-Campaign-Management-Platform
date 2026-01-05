'use client';

import { useAuth } from '@/contexts/AuthContext';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { Bell, Search, Menu, Settings, User, LogOut, HelpCircle, KeyRound, Mail, UserPlus, AlertCircle } from 'lucide-react';
import { Input } from '@/components/ui/input';
import Link from 'next/link';
import { useNotifications } from '@/hooks/useNotifications';
import { formatDistanceToNow } from 'date-fns';

interface HeaderProps {
  onMenuClick?: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const { user, logout } = useAuth();
  const { notifications, unreadCount, markAsRead, isConnected } = useNotifications();

  // Get notification icon based on type
  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'CAMPAIGN_SENT':
        return <Mail className="h-4 w-4 text-blue-500" />;
      case 'CONTACT_ADDED':
        return <UserPlus className="h-4 w-4 text-green-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-orange-500" />;
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

  // Handle notification click
  const handleNotificationClick = async (notificationId: string, isRead: boolean) => {
    if (!isRead) {
      await markAsRead(notificationId);
    }
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-background/80 px-4 backdrop-blur-xl sm:px-6">
      {/* Mobile menu button */}
      {onMenuClick && (
        <Button
          variant="ghost"
          size="icon"
          className="h-9 w-9 shrink-0 lg:hidden"
          onClick={onMenuClick}
        >
          <Menu className="h-5 w-5" />
          <span className="sr-only">Toggle menu</span>
        </Button>
      )}
      
      {/* Page title / Breadcrumb */}
      <div className="flex-1">
        <h1 className="text-lg font-semibold text-foreground sm:text-xl">
          {user?.organization?.name ? (
            <span className="flex items-center gap-2">
              <span className="hidden sm:inline text-muted-foreground font-normal">
                {user.organization.name}
              </span>
              <span className="hidden sm:inline text-muted-foreground/50">/</span>
              <span>Dashboard</span>
            </span>
          ) : (
            'Dashboard'
          )}
        </h1>
      </div>
      
      {/* Search bar - hidden on mobile */}
      <div className="hidden md:flex relative max-w-sm flex-1">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input 
          type="search"
          placeholder="Search campaigns, contacts..."
          className="h-9 w-full pl-9 bg-muted/50 border-0 focus-visible:ring-1"
        />
      </div>
      
      {/* Actions */}
      <div className="flex items-center gap-1 sm:gap-2">
        {/* Mobile search button */}
        <Button variant="ghost" size="icon" className="h-9 w-9 md:hidden">
          <Search className="h-5 w-5" />
        </Button>
        
        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="relative h-9 w-9">
              <Bell className="h-5 w-5" />
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-medium text-primary-foreground">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-80 p-0" align="end" forceMount>
            <div className="flex items-center justify-between border-b p-4">
              <h4 className="text-sm font-semibold">Notifications</h4>
              {unreadCount > 0 && (
                <span className="text-xs text-muted-foreground">{unreadCount} new</span>
              )}
            </div>
            <div className="max-h-80 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="p-8 text-center text-sm text-muted-foreground">
                  No notifications yet
                </div>
              ) : (
                <div className="space-y-1 p-2">
                  {notifications.slice(0, 5).map((notification) => (
                    <div 
                      key={notification.id}
                      onClick={() => handleNotificationClick(notification.id, notification.is_read)}
                      className={`flex gap-3 rounded-lg p-3 hover:bg-accent cursor-pointer transition-colors ${
                        !notification.is_read ? 'bg-accent/50' : ''
                      }`}
                    >
                      <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${getNotificationIconBg(notification.notification_type)}`}>
                        {getNotificationIcon(notification.notification_type)}
                      </div>
                      <div className="flex-1 space-y-1">
                        <p className="text-sm font-medium leading-none">{notification.title}</p>
                        <p className="text-xs text-muted-foreground line-clamp-2">{notification.message}</p>
                        <p className="text-xs text-muted-foreground">
                          {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                        </p>
                      </div>
                      {!notification.is_read && (
                        <div className="flex h-2 w-2 shrink-0 items-center justify-center rounded-full bg-primary mt-2" />
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="border-t p-2">
              <Link href="/dashboard/notifications" className="flex w-full items-center justify-center gap-2 rounded-lg p-2 text-sm font-medium hover:bg-accent transition-colors">
                View all notifications
              </Link>
            </div>
          </DropdownMenuContent>
        </DropdownMenu>
        
        {/* Theme toggle */}
        <ThemeToggle />
        
        {/* User menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button 
              variant="ghost" 
              className="relative h-9 w-9 rounded-full ring-2 ring-transparent transition-all hover:ring-primary/20"
            >
              <Avatar className="h-9 w-9">
                <AvatarImage
                  src={user?.profile_picture}
                  alt={user?.first_name}
                />
                <AvatarFallback className="gradient-bg text-white text-sm font-medium">
                  {user?.first_name?.[0]}{user?.last_name?.[0]}
                </AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-64 p-2" align="end" forceMount>
            <DropdownMenuLabel className="font-normal p-2">
              <div className="flex items-center gap-3">
                <Avatar className="h-10 w-10">
                  <AvatarImage src={user?.profile_picture} alt={user?.first_name} />
                  <AvatarFallback className="gradient-bg text-white">
                    {user?.first_name?.[0]}{user?.last_name?.[0]}
                  </AvatarFallback>
                </Avatar>
                <div className="flex flex-col space-y-0.5">
                  <p className="text-sm font-medium leading-none">
                    {user?.first_name} {user?.last_name}
                  </p>
                  <p className="text-xs leading-none text-muted-foreground">
                    {user?.email}
                  </p>
                </div>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator className="my-2" />
            <DropdownMenuItem asChild className="cursor-pointer gap-2 p-2 rounded-lg">
              <Link href="/dashboard/profile">
                <User className="h-4 w-4" />
                <span>Profile</span>
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild className="cursor-pointer gap-2 p-2 rounded-lg">
              <Link href="/dashboard/settings/providers">
                <Settings className="h-4 w-4" />
                <span>Settings</span>
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild className="cursor-pointer gap-2 p-2 rounded-lg">
              <Link href="/dashboard/settings">
                <KeyRound className="h-4 w-4" />
                <span>Change Password</span>
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem className="cursor-pointer gap-2 p-2 rounded-lg">
              <HelpCircle className="h-4 w-4" />
              <span>Help & Support</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator className="my-2" />
            <DropdownMenuItem 
              onClick={logout}
              className="cursor-pointer gap-2 p-2 rounded-lg text-destructive focus:text-destructive focus:bg-destructive/10"
            >
              <LogOut className="h-4 w-4" />
              <span>Log out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
