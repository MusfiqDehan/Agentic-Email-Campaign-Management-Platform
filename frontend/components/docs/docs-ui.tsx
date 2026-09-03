import type { ReactNode } from 'react';
import { AlertTriangle, Info, Lightbulb, ShieldAlert } from 'lucide-react';
import { cn } from '@/config/utils';

export function Section({
  id,
  title,
  lead,
  children,
}: {
  id: string;
  title: string;
  lead?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-24 border-t border-border pt-12 first:border-0 first:pt-0">
      <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">{title}</h2>
      {lead && <p className="mt-3 text-base leading-relaxed text-muted-foreground">{lead}</p>}
      <div className="mt-6 space-y-6">{children}</div>
    </section>
  );
}

export function SubHeading({ children }: { children: ReactNode }) {
  return <h3 className="text-lg font-semibold tracking-tight">{children}</h3>;
}

export function Prose({ children }: { children: ReactNode }) {
  return <p className="text-sm leading-relaxed text-muted-foreground sm:text-base">{children}</p>;
}

export function Steps({ children }: { children: ReactNode }) {
  return <ol className="space-y-4">{children}</ol>;
}

export function Step({ n, title, children }: { n: number; title: string; children?: ReactNode }) {
  return (
    <li className="flex gap-4">
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
        {n}
      </span>
      <div className="flex-1 pt-1">
        <p className="font-medium">{title}</p>
        {children && <div className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{children}</div>}
      </div>
    </li>
  );
}

export function Bullets({ children }: { children: ReactNode }) {
  return (
    <ul className="space-y-2 text-sm leading-relaxed text-muted-foreground sm:text-base">{children}</ul>
  );
}

export function Bullet({ children }: { children: ReactNode }) {
  return (
    <li className="flex gap-3">
      <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-primary/60" />
      <span className="flex-1">{children}</span>
    </li>
  );
}

const CALLOUT_STYLES = {
  note: {
    icon: Info,
    wrapper: 'border-purple-500/30 bg-purple-500/5',
    iconColor: 'text-purple-600 dark:text-purple-400',
  },
  tip: {
    icon: Lightbulb,
    wrapper: 'border-emerald-500/30 bg-emerald-500/5',
    iconColor: 'text-emerald-500',
  },
  warning: {
    icon: AlertTriangle,
    wrapper: 'border-amber-500/30 bg-amber-500/5',
    iconColor: 'text-amber-500',
  },
  security: {
    icon: ShieldAlert,
    wrapper: 'border-purple-500/30 bg-purple-500/5',
    iconColor: 'text-purple-500',
  },
} as const;

export function Callout({
  variant = 'note',
  title,
  children,
}: {
  variant?: keyof typeof CALLOUT_STYLES;
  title?: string;
  children: ReactNode;
}) {
  const style = CALLOUT_STYLES[variant];
  const Icon = style.icon;
  return (
    <div className={cn('flex gap-3 rounded-xl border p-4', style.wrapper)}>
      <Icon className={cn('mt-0.5 h-5 w-5 shrink-0', style.iconColor)} />
      <div className="flex-1 space-y-1">
        {title && <p className="text-sm font-semibold">{title}</p>}
        <div className="text-sm leading-relaxed text-muted-foreground">{children}</div>
      </div>
    </div>
  );
}

export function Code({ children }: { children: ReactNode }) {
  return (
    <code className="rounded-md bg-muted px-1.5 py-0.5 font-mono text-[0.85em] text-foreground">
      {children}
    </code>
  );
}

/**
 * Builds one `DataTable` row. Cells are passed as arguments rather than as an
 * array literal so that JSX cells are not mistaken for an unkeyed list — the
 * table assigns its own keys when it renders them.
 */
export function row(...cells: ReactNode[]): ReactNode[] {
  return cells;
}

export function DataTable({ headers, rows }: { headers: string[]; rows: ReactNode[][] }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="w-full text-left text-sm">
        <thead className="bg-muted/50">
          <tr>
            {headers.map((header) => (
              <th key={header} className="whitespace-nowrap px-4 py-3 font-semibold">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {rows.map((row, i) => (
            <tr key={i} className="align-top">
              {row.map((cell, j) => (
                <td key={j} className="px-4 py-3 text-muted-foreground">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function StatusPill({ tone, children }: { tone: 'green' | 'amber' | 'blue' | 'red' | 'purple' | 'gray'; children: ReactNode }) {
  const tones = {
    green: 'bg-green-500/10 text-green-600 dark:text-green-400',
    amber: 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
    blue: 'bg-purple-500/10 text-purple-600 dark:text-purple-400',
    purple: 'bg-purple-500/10 text-purple-600 dark:text-purple-400',
    red: 'bg-red-500/10 text-red-600 dark:text-red-400',
    gray: 'bg-muted text-muted-foreground',
  } as const;
  return (
    <span className={cn('inline-block whitespace-nowrap rounded-full px-2.5 py-0.5 font-mono text-xs font-medium', tones[tone])}>
      {children}
    </span>
  );
}
