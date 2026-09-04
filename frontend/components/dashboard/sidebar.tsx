'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/config/utils';
import {
  LogOut,
  ChevronLeft,
  Sparkles,
  Shield,
  UsersRound,
  BookOpen,
} from 'lucide-react';
import { useAuth, usePlatformAdmin, useOrgAdmin } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { BrandLogo } from '@/components/brand-logo';
import { UpgradeDialog } from '@/components/dashboard/upgrade-dialog';
import { fetchPackageCatalog, type PackageCatalog } from '@/services/packages';
import {
  isNavItemActive,
  orgAdminItems,
  platformAdminItems,
  sidebarItems,
  type NavItem,
} from '@/components/dashboard/nav-config';

interface SidebarProps {
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

function SidebarLink({
  item,
  collapsed,
  active,
  activeClassName,
  indicatorClassName,
}: {
  item: NavItem;
  collapsed: boolean;
  active: boolean;
  activeClassName: string;
  indicatorClassName: string;
}) {
  return (
    <Link
      href={item.href}
      aria-current={active ? 'page' : undefined}
      aria-label={collapsed ? item.title : undefined}
      title={collapsed ? item.title : undefined}
      className={cn(
        'group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        collapsed && 'justify-center px-2',
        active
          ? activeClassName
          : 'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground'
      )}
    >
      {active && (
        <div className={cn('absolute left-0 top-1/2 h-8 w-1 -translate-y-1/2 rounded-r-full', indicatorClassName)} aria-hidden="true" />
      )}

      <item.icon
        className={cn(
          'h-5 w-5 shrink-0 transition-colors',
          active ? '' : item.color
        )}
        aria-hidden="true"
      />

      {!collapsed && <span className="truncate">{item.title}</span>}
    </Link>
  );
}

export function Sidebar({ isCollapsed = false, onToggleCollapse }: SidebarProps) {
  const pathname = usePathname();
  const { logout, user } = useAuth();
  const isPlatformAdmin = usePlatformAdmin();
  const isOrgAdmin = useOrgAdmin();
  const [upgradeOpen, setUpgradeOpen] = useState(false);
  const [catalog, setCatalog] = useState<PackageCatalog | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchPackageCatalog()
      .then((data) => {
        if (!cancelled) setCatalog(data);
      })
      .catch(() => {
        if (!cancelled) setCatalog(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const showUpgradeCta = catalog?.can_upgrade === true;

  return (
    <>
      <aside
        className={cn(
          'relative z-0 hidden h-full shrink-0 flex-col border-r border-sidebar-border bg-sidebar transition-[width] duration-300 ease-in-out lg:flex',
          isCollapsed ? 'w-[72px]' : 'w-64'
        )}
        aria-label="Sidebar"
      >
        <div
          className={cn(
            'flex h-16 items-center border-b border-sidebar-border px-4',
            isCollapsed ? 'justify-center' : 'justify-between'
          )}
        >
          <Link href="/dashboard" className="transition-transform hover:scale-105">
            <BrandLogo
              size={32}
              showWordmark={!isCollapsed}
              wordmarkClassName="text-[15px] text-sidebar-foreground"
            />
          </Link>

          {onToggleCollapse && !isCollapsed && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={onToggleCollapse}
              aria-label="Collapse sidebar"
            >
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
            </Button>
          )}
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto p-3" aria-label="Dashboard">
          {sidebarItems.map((item) => (
            <SidebarLink
              key={item.href}
              item={item}
              collapsed={isCollapsed}
              active={isNavItemActive(pathname, item.href)}
              activeClassName="bg-primary/10 text-primary shadow-sm"
              indicatorClassName="bg-primary"
            />
          ))}

          {isPlatformAdmin && (
            <>
              {!isCollapsed ? (
                <div className="mb-2 mt-4 px-3">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    <Shield className="h-3.5 w-3.5" aria-hidden="true" />
                    <span>Platform Admin</span>
                  </div>
                  <div className="mt-1 h-px bg-border" />
                </div>
              ) : (
                <div className="mx-3 my-2 h-px bg-border" role="separator" />
              )}
              {platformAdminItems.map((item) => (
                <SidebarLink
                  key={item.href}
                  item={item}
                  collapsed={isCollapsed}
                  active={isNavItemActive(pathname, item.href)}
                  activeClassName="bg-purple-500/10 text-purple-600 shadow-sm"
                  indicatorClassName="bg-purple-600"
                />
              ))}
            </>
          )}

          {isOrgAdmin && !isPlatformAdmin && (
            <>
              {!isCollapsed ? (
                <div className="mb-2 mt-4 px-3">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    <UsersRound className="h-3.5 w-3.5" aria-hidden="true" />
                    <span>Organization Admin</span>
                  </div>
                  <div className="mt-1 h-px bg-border" />
                </div>
              ) : (
                <div className="mx-3 my-2 h-px bg-border" role="separator" />
              )}
              {orgAdminItems.map((item) => (
                <SidebarLink
                  key={item.href}
                  item={item}
                  collapsed={isCollapsed}
                  active={isNavItemActive(pathname, item.href)}
                  activeClassName="bg-teal-500/10 text-teal-600 shadow-sm"
                  indicatorClassName="bg-teal-500"
                />
              ))}
            </>
          )}
        </nav>

        <div className="border-t border-sidebar-border p-3">
          {showUpgradeCta && !isCollapsed && (
            <button
              type="button"
              onClick={() => setUpgradeOpen(true)}
              className="mb-3 w-full rounded-xl bg-gradient-to-br from-primary/10 to-purple-500/10 p-3 text-left transition-colors hover:from-primary/15 hover:to-purple-500/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary" aria-hidden="true" />
                <span className="text-xs font-medium">Upgrade to Pro</span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">Get advanced features</p>
            </button>
          )}
          {showUpgradeCta && isCollapsed && (
            <Button
              variant="ghost"
              size="icon"
              className="mb-3 w-full"
              onClick={() => setUpgradeOpen(true)}
              aria-label="Upgrade to Pro"
            >
              <Sparkles className="h-4 w-4 text-primary" aria-hidden="true" />
            </Button>
          )}

          {!isCollapsed && user && (
            <div className="mb-3 flex items-center gap-3 rounded-lg p-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full gradient-bg text-xs font-medium text-white" aria-hidden="true">
                {user.first_name?.[0]}
                {user.last_name?.[0]}
              </div>
              <div className="flex-1 overflow-hidden">
                <p className="truncate text-sm font-medium text-sidebar-foreground">
                  {user.first_name} {user.last_name}
                </p>
                <p className="truncate text-xs text-muted-foreground">{user.email}</p>
              </div>
            </div>
          )}

          <Link
            href="/docs"
            target="_blank"
            rel="noreferrer"
            aria-label={isCollapsed ? 'Documentation' : undefined}
            title={isCollapsed ? 'Documentation' : undefined}
            className={cn(
              'group relative mb-1 flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-sidebar-foreground/70 transition-all duration-200 hover:bg-sidebar-accent hover:text-sidebar-foreground',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
              isCollapsed && 'justify-center px-2'
            )}
          >
            <BookOpen className="h-5 w-5 shrink-0 text-amber-500" aria-hidden="true" />
            {!isCollapsed && <span className="truncate">Documentation</span>}
          </Link>

          <Button
            variant="ghost"
            className={cn(
              'w-full justify-start gap-3 text-sidebar-foreground/70 hover:bg-destructive/10 hover:text-destructive',
              isCollapsed && 'justify-center px-2'
            )}
            onClick={logout}
            aria-label={isCollapsed ? 'Logout' : undefined}
          >
            <LogOut className="h-5 w-5" aria-hidden="true" />
            {!isCollapsed && <span>Logout</span>}
          </Button>

          {isCollapsed && onToggleCollapse && (
            <Button
              variant="ghost"
              size="icon"
              className="mt-2 w-full"
              onClick={onToggleCollapse}
              aria-label="Expand sidebar"
            >
              <ChevronLeft className="h-4 w-4 rotate-180" aria-hidden="true" />
            </Button>
          )}
        </div>
      </aside>
      <UpgradeDialog
        open={upgradeOpen}
        onOpenChange={setUpgradeOpen}
        catalog={catalog}
        onCatalogChange={setCatalog}
      />
    </>
  );
}
