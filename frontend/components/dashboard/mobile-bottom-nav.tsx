'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BookOpen, Ellipsis, Settings, Sparkles, X } from 'lucide-react';
import { useAuth, useOrgAdmin, usePlatformAdmin } from '@/contexts/AuthContext';
import { BottomNavBar, BottomNavItem } from '@/components/ui/bottom-nav';
import {
  Dialog,
  DialogDescription,
  DialogHeader,
  DialogOverlay,
  DialogPortal,
  DialogTitle,
} from '@/components/ui/dialog';
import * as DialogPrimitive from '@radix-ui/react-dialog';
import { cn } from '@/config/utils';
import { UpgradeDialog } from '@/components/dashboard/upgrade-dialog';
import { fetchPackageCatalog, type PackageCatalog } from '@/services/packages';
import {
  isNavItemActive,
  mobilePrimaryHrefs,
  orgAdminItems,
  platformAdminItems,
  sidebarItems,
  type NavItem,
} from '@/components/dashboard/nav-config';

function MoreSheetItem({
  item,
  active,
  onNavigate,
  variant = 'default',
}: {
  item: NavItem;
  active: boolean;
  onNavigate: () => void;
  variant?: 'default' | 'admin' | 'org';
}) {
  const activeClass =
    variant === 'admin'
      ? 'bg-red-500/10 text-red-600'
      : variant === 'org'
        ? 'bg-teal-500/10 text-teal-600'
        : 'bg-primary/10 text-primary';

  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      aria-current={active ? 'page' : undefined}
      className={cn(
        'flex min-h-16 flex-col items-center justify-center gap-1 rounded-xl px-2 py-2 text-center text-xs font-medium transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        active ? activeClass : 'text-muted-foreground hover:bg-muted hover:text-foreground'
      )}
    >
      <item.icon
        className={cn('h-5 w-5', active ? '' : item.color)}
        aria-hidden="true"
      />
      <span className="line-clamp-2">{item.shortTitle ?? item.title}</span>
    </Link>
  );
}

export function MobileBottomNav() {
  const pathname = usePathname();
  const { user } = useAuth();
  const isPlatformAdmin = usePlatformAdmin();
  const isOrgAdmin = useOrgAdmin();
  const [moreOpen, setMoreOpen] = useState(false);
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

  const primaryItems = sidebarItems.filter((item) =>
    (mobilePrimaryHrefs as readonly string[]).includes(item.href)
  );
  const moreMainItems = sidebarItems.filter(
    (item) => !(mobilePrimaryHrefs as readonly string[]).includes(item.href)
  );

  const moreActive = useMemo(() => {
    const extraHrefs = [
      ...sidebarItems
        .filter((item) => !(mobilePrimaryHrefs as readonly string[]).includes(item.href))
        .map((item) => item.href),
      ...(isPlatformAdmin ? platformAdminItems.map((item) => item.href) : []),
      ...(isOrgAdmin && !isPlatformAdmin ? orgAdminItems.map((item) => item.href) : []),
      '/dashboard/settings',
      '/dashboard/profile',
    ];
    return extraHrefs.some((href) => isNavItemActive(pathname, href));
  }, [isOrgAdmin, isPlatformAdmin, pathname]);

  const showUpgradeCta = catalog?.can_upgrade === true;
  const closeMore = () => setMoreOpen(false);

  return (
    <>
      <BottomNavBar label="Dashboard">
        {primaryItems.map((item) => (
          <BottomNavItem
            key={item.href}
            href={item.href}
            icon={item.icon}
            label={item.shortTitle ?? item.title}
            active={isNavItemActive(pathname, item.href)}
          />
        ))}
        <BottomNavItem
          icon={Ellipsis}
          label="More"
          active={moreActive || moreOpen}
          onClick={() => setMoreOpen(true)}
          ariaExpanded={moreOpen}
          ariaHasPopup="dialog"
          ariaControls="dashboard-more-sheet"
        />
      </BottomNavBar>

      <Dialog open={moreOpen} onOpenChange={setMoreOpen}>
        <DialogPortal>
          <DialogOverlay />
          <DialogPrimitive.Content
            id="dashboard-more-sheet"
            className={cn(
              'fixed inset-x-0 bottom-0 z-50 flex max-h-[min(80vh,32rem)] w-full flex-col rounded-t-2xl border border-border bg-background shadow-2xl',
              'pb-[env(safe-area-inset-bottom,0px)]',
              'data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0',
              'data-[state=closed]:slide-out-to-bottom data-[state=open]:slide-in-from-bottom',
              'duration-200 focus:outline-none'
            )}
          >
            <DialogHeader className="relative border-b border-border px-4 py-3 pr-12 text-left">
              <DialogTitle>More</DialogTitle>
              <DialogDescription className="sr-only">
                Additional dashboard and admin destinations
              </DialogDescription>
              <DialogPrimitive.Close className="absolute right-3 top-3 rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                <X className="h-4 w-4" aria-hidden="true" />
                <span className="sr-only">Close</span>
              </DialogPrimitive.Close>
            </DialogHeader>

            <div className="overflow-y-auto px-3 py-3">
              <p className="mb-2 px-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Workspace
              </p>
              <div className="grid grid-cols-4 gap-1 sm:grid-cols-5">
                {moreMainItems.map((item) => (
                  <MoreSheetItem
                    key={item.href}
                    item={item}
                    active={isNavItemActive(pathname, item.href)}
                    onNavigate={closeMore}
                  />
                ))}
                <Link
                  href="/dashboard/settings"
                  onClick={closeMore}
                  aria-current={pathname.startsWith('/dashboard/settings') ? 'page' : undefined}
                  className={cn(
                    'flex min-h-16 flex-col items-center justify-center gap-1 rounded-xl px-2 py-2 text-center text-xs font-medium transition-colors',
                    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                    pathname.startsWith('/dashboard/settings')
                      ? 'bg-primary/10 text-primary'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  )}
                >
                  <Settings className="h-5 w-5 text-slate-500" aria-hidden="true" />
                  <span>Settings</span>
                </Link>
                <Link
                  href="/docs"
                  target="_blank"
                  rel="noreferrer"
                  onClick={closeMore}
                  className="flex min-h-16 flex-col items-center justify-center gap-1 rounded-xl px-2 py-2 text-center text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <BookOpen className="h-5 w-5 text-amber-500" aria-hidden="true" />
                  <span>Docs</span>
                </Link>
              </div>

              {isPlatformAdmin && (
                <>
                  <p className="mb-2 mt-4 px-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Platform admin
                  </p>
                  <div className="grid grid-cols-4 gap-1 sm:grid-cols-5">
                    {platformAdminItems.map((item) => (
                      <MoreSheetItem
                        key={item.href}
                        item={item}
                        active={isNavItemActive(pathname, item.href)}
                        onNavigate={closeMore}
                        variant="admin"
                      />
                    ))}
                  </div>
                </>
              )}

              {isOrgAdmin && !isPlatformAdmin && (
                <>
                  <p className="mb-2 mt-4 px-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Organization
                  </p>
                  <div className="grid grid-cols-4 gap-1 sm:grid-cols-5">
                    {orgAdminItems.map((item) => (
                      <MoreSheetItem
                        key={item.href}
                        item={item}
                        active={isNavItemActive(pathname, item.href)}
                        onNavigate={closeMore}
                        variant="org"
                      />
                    ))}
                  </div>
                </>
              )}

              {showUpgradeCta && (
                <button
                  type="button"
                  onClick={() => {
                    closeMore();
                    setUpgradeOpen(true);
                  }}
                  className="mt-4 flex w-full items-center gap-3 rounded-xl bg-gradient-to-br from-primary/10 to-purple-500/10 p-3 text-left transition-colors hover:from-primary/15 hover:to-purple-500/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <Sparkles className="h-5 w-5 text-primary" aria-hidden="true" />
                  <span>
                    <span className="block text-sm font-medium">Upgrade to Pro</span>
                    <span className="block text-xs text-muted-foreground">Get advanced features</span>
                  </span>
                </button>
              )}

              {user && (
                <p className="mt-4 truncate px-1 text-xs text-muted-foreground">
                  Signed in as {user.first_name} {user.last_name}
                </p>
              )}
            </div>
          </DialogPrimitive.Content>
        </DialogPortal>
      </Dialog>

      <UpgradeDialog
        open={upgradeOpen}
        onOpenChange={setUpgradeOpen}
        catalog={catalog}
        onCatalogChange={setCatalog}
      />
    </>
  );
}
