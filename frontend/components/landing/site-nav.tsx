'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  ArrowRight,
  BookOpen,
  CreditCard,
  LogIn,
  Sparkles,
  Workflow,
} from 'lucide-react';
import { BrandLogo } from '@/components/brand-logo';
import { Button } from '@/components/ui/button';
import { BottomNavBar, BottomNavItem } from '@/components/ui/bottom-nav';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { SkipLink } from '@/components/skip-link';
import { cn } from '@/config/utils';

const marketingLinks = [
  { href: '/#how-it-works', hash: '#how-it-works', label: 'How it works', icon: Workflow },
  { href: '/#features', hash: '#features', label: 'Features', icon: Sparkles },
  { href: '/#pricing', hash: '#pricing', label: 'Pricing', icon: CreditCard },
  { href: '/docs', hash: null, label: 'Docs', icon: BookOpen },
] as const;

type SiteNavProps = {
  variant?: 'home' | 'docs';
};

export function SiteNav({ variant = 'home' }: SiteNavProps) {
  const pathname = usePathname();
  const [hash, setHash] = useState('');

  useEffect(() => {
    const syncHash = () => setHash(window.location.hash);
    syncHash();
    window.addEventListener('hashchange', syncHash);
    return () => window.removeEventListener('hashchange', syncHash);
  }, [pathname]);

  const isLinkActive = (href: string, linkHash: string | null) => {
    if (href === '/docs') {
      return pathname === '/docs' || pathname.startsWith('/docs/');
    }
    if (pathname !== '/') {
      return false;
    }
    return Boolean(linkHash) && hash === linkHash;
  };

  return (
    <>
      <SkipLink />
      <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <Link href="/" className="transition-transform hover:scale-105">
              <BrandLogo size={36} wordmarkClassName="sr-only sm:not-sr-only text-xl" priority />
            </Link>
            {variant === 'docs' && (
              <span className="hidden rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-semibold text-primary sm:inline-block">
                Docs
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 sm:gap-4">
            <nav aria-label="Primary" className="mr-2 hidden items-center gap-6 text-sm font-medium text-muted-foreground lg:flex">
              {marketingLinks.map((link) => {
                const active = isLinkActive(link.href, link.hash);
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={cn(
                      'transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-sm',
                      active && 'text-foreground'
                    )}
                    aria-current={active ? 'page' : undefined}
                  >
                    {link.label}
                  </Link>
                );
              })}
            </nav>
            <ThemeToggle />
            <Link href="/login" className="hidden lg:inline-flex">
              <Button variant="ghost">Log in</Button>
            </Link>
            <Link href="/signup">
              <Button className="gradient-bg h-9 border-0 px-3 text-white shadow-lg shadow-primary/25 transition-all hover:shadow-xl hover:shadow-primary/30 hover:scale-105 sm:h-10 sm:px-5">
                Get Started
                <ArrowRight className="ml-2 hidden h-4 w-4 sm:inline" aria-hidden="true" />
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <BottomNavBar label="Primary">
        {marketingLinks.map((link) => (
          <BottomNavItem
            key={link.href}
            href={link.href}
            icon={link.icon}
            label={link.label}
            active={isLinkActive(link.href, link.hash)}
          />
        ))}
        <BottomNavItem href="/login" icon={LogIn} label="Log in" />
      </BottomNavBar>
    </>
  );
}
