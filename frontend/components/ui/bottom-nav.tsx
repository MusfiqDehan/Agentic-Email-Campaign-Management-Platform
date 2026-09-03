'use client';

import Link from 'next/link';
import type { LucideIcon } from 'lucide-react';
import { cn } from '@/config/utils';

export function BottomNavBar({
  children,
  label,
  className,
}: {
  children: React.ReactNode;
  label: string;
  className?: string;
}) {
  return (
    <nav
      aria-label={label}
      className={cn(
        'fixed inset-x-0 bottom-0 z-50 border-t border-border bg-background/95 backdrop-blur-xl supports-[backdrop-filter]:bg-background/80 lg:hidden',
        'pb-[env(safe-area-inset-bottom,0px)]',
        className
      )}
    >
      <div className="flex min-h-16 items-stretch justify-around px-0.5">{children}</div>
    </nav>
  );
}

type BottomNavItemProps = {
  icon: LucideIcon;
  label: string;
  active?: boolean;
  href?: string;
  onClick?: () => void;
  ariaExpanded?: boolean;
  ariaHasPopup?: boolean | 'dialog' | 'menu';
  ariaControls?: string;
};

export function BottomNavItem({
  icon: Icon,
  label,
  active = false,
  href,
  onClick,
  ariaExpanded,
  ariaHasPopup,
  ariaControls,
}: BottomNavItemProps) {
  const className = cn(
    'flex min-h-16 min-w-0 flex-1 flex-col items-center justify-center gap-0.5 px-1 py-1.5 text-center text-[10px] font-medium leading-tight touch-manipulation sm:text-[11px]',
    'transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset',
    active ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
  );

  const content = (
    <>
      <Icon className="h-5 w-5 shrink-0" aria-hidden="true" />
      <span className="line-clamp-2 max-w-full">{label}</span>
    </>
  );

  if (href) {
    return (
      <Link
        href={href}
        onClick={onClick}
        className={className}
        aria-current={active ? 'page' : undefined}
      >
        {content}
      </Link>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className={className}
      aria-current={active ? 'true' : undefined}
      aria-expanded={ariaExpanded}
      aria-haspopup={ariaHasPopup}
      aria-controls={ariaControls}
    >
      {content}
    </button>
  );
}
