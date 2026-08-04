'use client';

import { useEffect, useState } from 'react';
import { BookOpen, ChevronDown } from 'lucide-react';
import { cn } from '@/config/utils';
import { DOC_GROUPS, DOC_SECTIONS } from '@/app/docs/sections';

/**
 * Highlights the section currently in view. Uses a top-biased root margin so the
 * heading nearest the top of the viewport wins rather than whichever intersects first.
 */
function useActiveSection() {
  const [activeId, setActiveId] = useState(DOC_SECTIONS[0].id);

  useEffect(() => {
    const headings = DOC_SECTIONS.map((section) => document.getElementById(section.id)).filter(
      (el): el is HTMLElement => el !== null
    );

    if (headings.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);

        if (visible.length > 0) {
          setActiveId(visible[0].target.id);
        }
      },
      { rootMargin: '-80px 0px -70% 0px', threshold: 0 }
    );

    headings.forEach((heading) => observer.observe(heading));
    return () => observer.disconnect();
  }, []);

  return activeId;
}

function NavLinks({ activeId, onNavigate }: { activeId: string; onNavigate?: () => void }) {
  return (
    <nav className="space-y-6">
      {DOC_GROUPS.map((group) => (
        <div key={group.group}>
          <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {group.group}
          </p>
          <ul className="space-y-0.5">
            {group.sections.map((section) => {
              const active = activeId === section.id;
              return (
                <li key={section.id}>
                  <a
                    href={`#${section.id}`}
                    onClick={onNavigate}
                    className={cn(
                      'relative block rounded-lg px-3 py-1.5 text-sm transition-colors',
                      active
                        ? 'bg-primary/10 font-medium text-primary'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    )}
                  >
                    {active && (
                      <span className="absolute left-0 top-1/2 h-4 w-0.5 -translate-y-1/2 rounded-r-full bg-primary" />
                    )}
                    {section.navLabel ?? section.title}
                  </a>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );
}

export function DocsSidebar() {
  const activeId = useActiveSection();

  return (
    <aside className="hidden w-64 shrink-0 lg:block">
      <div className="sticky top-24 max-h-[calc(100vh-8rem)] overflow-y-auto pb-10 pr-2">
        <NavLinks activeId={activeId} />
      </div>
    </aside>
  );
}

export function DocsMobileNav() {
  const activeId = useActiveSection();
  const [open, setOpen] = useState(false);
  const activeSection = DOC_SECTIONS.find((section) => section.id === activeId);

  return (
    <div className="sticky top-16 z-30 -mx-4 mb-8 border-b border-border bg-background/90 px-4 py-3 backdrop-blur-xl lg:hidden">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-center justify-between rounded-xl border border-border bg-card px-4 py-2.5 text-sm font-medium"
        aria-expanded={open}
      >
        <span className="flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-primary" />
          <span className="truncate">{activeSection?.navLabel ?? activeSection?.title ?? 'Contents'}</span>
        </span>
        <ChevronDown className={cn('h-4 w-4 shrink-0 transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <div className="mt-2 max-h-[60vh] overflow-y-auto rounded-xl border border-border bg-card p-3 shadow-lg">
          <NavLinks activeId={activeId} onNavigate={() => setOpen(false)} />
        </div>
      )}
    </div>
  );
}
