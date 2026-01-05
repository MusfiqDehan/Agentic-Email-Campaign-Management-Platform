'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/config/utils';
import {
  LayoutDashboard,
  Mail,
  Users,
  Settings,
  FileText,
  Send,
  LogOut,
  User,
  Menu,
  X,
  ChevronLeft,
  Sparkles,
  Shield,
  Building2,
  Bell,
  UsersRound,
  CheckSquare
} from 'lucide-react';
import { useAuth, usePlatformAdmin, useOrgAdmin } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';

const sidebarItems = [
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
    color: 'text-blue-500'
  },
  {
    title: 'Campaigns',
    href: '/dashboard/campaigns',
    icon: Send,
    color: 'text-green-500'
  },
  {
    title: 'Contacts',
    href: '/dashboard/contacts',
    icon: Users,
    color: 'text-purple-500'
  },
  {
    title: 'Templates',
    href: '/dashboard/templates',
    icon: FileText,
    color: 'text-orange-500'
  },
];

const platformAdminItems = [
  {
    title: 'Admin Panel',
    href: '/dashboard/admin',
    icon: Shield,
    color: 'text-red-500'
  },
  {
    title: 'Organizations',
    href: '/dashboard/admin/organizations',
    icon: Building2,
    color: 'text-indigo-500'
  },
  {
    title: 'Global Templates',
    href: '/dashboard/admin/templates',
    icon: FileText,
    color: 'text-cyan-500'
  },
  {
    title: 'Pending Approvals',
    href: '/dashboard/admin/approvals',
    icon: CheckSquare,
    color: 'text-amber-500'
  },
];

const orgAdminItems = [
  {
    title: 'Team Insights',
    href: '/dashboard/team',
    icon: UsersRound,
    color: 'text-teal-500'
  },
];

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export function Sidebar({ isOpen = true, onClose, isCollapsed = false, onToggleCollapse }: SidebarProps) {
  const pathname = usePathname();
  const { logout, user } = useAuth();
  const isPlatformAdmin = usePlatformAdmin();
  const isOrgAdmin = useOrgAdmin();

  const isActive = (href: string) => {
    if (href === '/dashboard') {
      return pathname === '/dashboard';
    }
    return pathname === href || pathname.startsWith(href + '/');
  };

  if (typeof window === 'undefined') return null;

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <aside
        className={cn(
          "fixed left-0 top-0 z-50 flex h-full flex-col border-r border-sidebar-border bg-sidebar transition-all duration-300 ease-in-out lg:relative lg:z-0",
          isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
          isCollapsed ? "w-[72px]" : "w-64"
        )}
      >
        {/* Logo section */}
        <div className={cn(
          "flex h-16 items-center border-b border-sidebar-border px-4",
          isCollapsed ? "justify-center" : "justify-between"
        )}>
          <Link 
            href="/dashboard" 
            className={cn(
              "flex items-center gap-2.5 font-bold transition-transform hover:scale-105",
              isCollapsed && "justify-center"
            )}
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl gradient-bg shadow-lg shadow-primary/20">
              <Mail className="h-5 w-5 text-white" />
            </div>
            {!isCollapsed && (
              <span className="text-lg text-sidebar-foreground">EmailCampaign</span>
            )}
          </Link>
          
          {/* Close button on mobile */}
          {onClose && !isCollapsed && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 lg:hidden"
              onClick={onClose}
            >
              <X className="h-5 w-5" />
            </Button>
          )}
          
          {/* Collapse button on desktop */}
          {onToggleCollapse && !isCollapsed && (
            <Button
              variant="ghost"
              size="icon"
              className="hidden h-8 w-8 lg:flex"
              onClick={onToggleCollapse}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
          )}
        </div>
        
        {/* Navigation */}
        <nav className="flex-1 space-y-1 overflow-y-auto p-3">
          {/* Main Navigation */}
          {sidebarItems.map((item) => {
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={cn(
                  "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
                  isCollapsed && "justify-center px-2",
                  active 
                    ? "bg-primary/10 text-primary shadow-sm" 
                    : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground"
                )}
              >
                {/* Active indicator */}
                {active && (
                  <div className="absolute left-0 top-1/2 h-8 w-1 -translate-y-1/2 rounded-r-full bg-primary" />
                )}
                
                <item.icon className={cn(
                  "h-5 w-5 shrink-0 transition-colors",
                  active ? "text-primary" : item.color
                )} />
                
                {!isCollapsed && (
                  <span className="truncate">{item.title}</span>
                )}
                
                {/* Tooltip for collapsed state */}
                {isCollapsed && (
                  <div className="absolute left-full ml-2 hidden rounded-lg bg-popover px-3 py-2 text-sm font-medium text-popover-foreground shadow-lg group-hover:block">
                    {item.title}
                  </div>
                )}
              </Link>
            );
          })}

          {/* Platform Admin Section */}
          {isPlatformAdmin && (
            <>
              {!isCollapsed && (
                <div className="mt-4 mb-2 px-3">
                  <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    <Shield className="h-3.5 w-3.5" />
                    <span>Platform Admin</span>
                  </div>
                  <div className="mt-1 h-px bg-border" />
                </div>
              )}
              {isCollapsed && (
                <div className="my-2 mx-3 h-px bg-border" />
              )}
              {platformAdminItems.map((item) => {
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={onClose}
                    className={cn(
                      "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
                      isCollapsed && "justify-center px-2",
                      active 
                        ? "bg-red-500/10 text-red-600 shadow-sm" 
                        : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground"
                    )}
                  >
                    {active && (
                      <div className="absolute left-0 top-1/2 h-8 w-1 -translate-y-1/2 rounded-r-full bg-red-500" />
                    )}
                    
                    <item.icon className={cn(
                      "h-5 w-5 shrink-0 transition-colors",
                      active ? "text-red-600" : item.color
                    )} />
                    
                    {!isCollapsed && (
                      <span className="truncate">{item.title}</span>
                    )}
                    
                    {isCollapsed && (
                      <div className="absolute left-full ml-2 hidden rounded-lg bg-popover px-3 py-2 text-sm font-medium text-popover-foreground shadow-lg group-hover:block">
                        {item.title}
                      </div>
                    )}
                  </Link>
                );
              })}
            </>
          )}

          {/* Organization Admin Section */}
          {isOrgAdmin && !isPlatformAdmin && (
            <>
              {!isCollapsed && (
                <div className="mt-4 mb-2 px-3">
                  <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    <UsersRound className="h-3.5 w-3.5" />
                    <span>Organization Admin</span>
                  </div>
                  <div className="mt-1 h-px bg-border" />
                </div>
              )}
              {isCollapsed && (
                <div className="my-2 mx-3 h-px bg-border" />
              )}
              {orgAdminItems.map((item) => {
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={onClose}
                    className={cn(
                      "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
                      isCollapsed && "justify-center px-2",
                      active 
                        ? "bg-teal-500/10 text-teal-600 shadow-sm" 
                        : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground"
                    )}
                  >
                    {active && (
                      <div className="absolute left-0 top-1/2 h-8 w-1 -translate-y-1/2 rounded-r-full bg-teal-500" />
                    )}
                    
                    <item.icon className={cn(
                      "h-5 w-5 shrink-0 transition-colors",
                      active ? "text-teal-600" : item.color
                    )} />
                    
                    {!isCollapsed && (
                      <span className="truncate">{item.title}</span>
                    )}
                    
                    {isCollapsed && (
                      <div className="absolute left-full ml-2 hidden rounded-lg bg-popover px-3 py-2 text-sm font-medium text-popover-foreground shadow-lg group-hover:block">
                        {item.title}
                      </div>
                    )}
                  </Link>
                );
              })}
            </>
          )}
        </nav>
        
        {/* User section */}
        <div className="border-t border-sidebar-border p-3">
          {/* Pro upgrade banner */}
          {!isCollapsed && (
            <div className="mb-3 rounded-xl bg-gradient-to-br from-primary/10 to-purple-500/10 p-3">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary" />
                <span className="text-xs font-medium">Upgrade to Pro</span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                Get advanced features
              </p>
            </div>
          )}
          
          {/* User info */}
          {!isCollapsed && user && (
            <div className="mb-3 flex items-center gap-3 rounded-lg p-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full gradient-bg text-xs font-medium text-white">
                {user.first_name?.[0]}{user.last_name?.[0]}
              </div>
              <div className="flex-1 overflow-hidden">
                <p className="truncate text-sm font-medium text-sidebar-foreground">
                  {user.first_name} {user.last_name}
                </p>
                <p className="truncate text-xs text-muted-foreground">
                  {user.email}
                </p>
              </div>
            </div>
          )}
          
          {/* Logout button */}
          <Button 
            variant="ghost" 
            className={cn(
              "w-full justify-start gap-3 text-sidebar-foreground/70 hover:bg-destructive/10 hover:text-destructive",
              isCollapsed && "justify-center px-2"
            )}
            onClick={logout}
          >
            <LogOut className="h-5 w-5" />
            {!isCollapsed && <span>Logout</span>}
          </Button>
          
          {/* Expand button when collapsed */}
          {isCollapsed && onToggleCollapse && (
            <Button
              variant="ghost"
              size="icon"
              className="mt-2 w-full"
              onClick={onToggleCollapse}
            >
              <ChevronLeft className="h-4 w-4 rotate-180" />
            </Button>
          )}
        </div>
      </aside>
    </>
  );
}

// Mobile menu button component
export function MobileMenuButton({ onClick }: { onClick: () => void }) {
  return (
    <Button
      variant="ghost"
      size="icon"
      className="h-9 w-9 lg:hidden"
      onClick={onClick}
    >
      <Menu className="h-5 w-5" />
    </Button>
  );
}
