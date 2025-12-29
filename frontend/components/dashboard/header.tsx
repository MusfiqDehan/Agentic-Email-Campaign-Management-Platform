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
import { Bell, Search, Menu, Settings, User, LogOut, HelpCircle } from 'lucide-react';
import { Input } from '@/components/ui/input';
import Link from 'next/link';

interface HeaderProps {
  onMenuClick?: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const { user, logout } = useAuth();

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
        <Button variant="ghost" size="icon" className="relative h-9 w-9">
          <Bell className="h-5 w-5" />
          <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-medium text-primary-foreground">
            3
          </span>
        </Button>
        
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
