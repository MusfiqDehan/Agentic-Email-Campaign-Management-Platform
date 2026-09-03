'use client';

import { TrendingUp, Users, Send, CheckCircle2, MoreHorizontal, ArrowUpRight } from 'lucide-react';

export function DashboardPreview() {
  return (
    <div className="relative mx-auto w-full max-w-5xl rounded-2xl border border-border/80 bg-card p-3 shadow-2xl shadow-rose-500/10 sm:p-5 lg:p-6 dark:border-border dark:shadow-none">
      {/* Window Mockup Header */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-border/60 pb-3">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <span className="h-3 w-3 rounded-full bg-rose-400" />
            <span className="h-3 w-3 rounded-full bg-amber-400" />
            <span className="h-3 w-3 rounded-full bg-emerald-400" />
          </div>
          <span className="ml-2 hidden text-xs font-medium text-muted-foreground sm:inline-block">
            app.emailcampaign.io/dashboard/analytics
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-50 px-2.5 py-1 font-medium text-rose-600 dark:bg-rose-950/40 dark:text-rose-400">
            <span className="h-1.5 w-1.5 rounded-full bg-rose-500 animate-pulse" />
            Live Syncing
          </span>
          <span className="hidden text-muted-foreground md:inline">Last updated 2m ago</span>
        </div>
      </div>

      {/* Top 3 KPI Cards */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 sm:gap-4">
        {/* KPI 1 */}
        <div className="rounded-xl border border-border/60 bg-background/60 p-3 sm:p-4">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Total Contacts</span>
            <Users className="h-4 w-4 text-rose-500" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">42,850</span>
            <span className="inline-flex items-center text-xs font-semibold text-emerald-600 dark:text-emerald-400">
              <ArrowUpRight className="h-3 w-3" /> +18.4%
            </span>
          </div>
          {/* Sparkline mini */}
          <div className="mt-3 flex h-8 items-end gap-1">
            {[35, 45, 40, 60, 55, 70, 65, 80, 75, 95].map((val, idx) => (
              <span
                key={idx}
                className="flex-1 rounded-t bg-rose-100 transition-all dark:bg-rose-950/60"
                style={{ height: `${val}%` }}
              />
            ))}
          </div>
        </div>

        {/* KPI 2 */}
        <div className="rounded-xl border border-border/60 bg-background/60 p-3 sm:p-4">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Emails Delivered</span>
            <Send className="h-4 w-4 text-rose-500" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">294.1k</span>
            <span className="inline-flex items-center text-xs font-semibold text-emerald-600 dark:text-emerald-400">
              <ArrowUpRight className="h-3 w-3" /> +24.8%
            </span>
          </div>
          {/* Mini pulse curve */}
          <div className="mt-3 flex h-8 items-end gap-1">
            {[40, 50, 48, 65, 72, 80, 85, 92, 88, 98].map((val, idx) => (
              <span
                key={idx}
                className="flex-1 rounded-t bg-rose-500/80 transition-all"
                style={{ height: `${val}%` }}
              />
            ))}
          </div>
        </div>

        {/* KPI 3 */}
        <div className="rounded-xl border border-border/60 bg-background/60 p-3 sm:p-4">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Avg. Open Rate</span>
            <TrendingUp className="h-4 w-4 text-rose-500" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">58.4%</span>
            <span className="inline-flex items-center text-xs font-semibold text-rose-500">
              Industry: 21%
            </span>
          </div>
          {/* Progress bar */}
          <div className="mt-4">
            <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
              <div className="h-full w-[58.4%] rounded-full bg-gradient-to-r from-rose-500 to-pink-500" />
            </div>
            <div className="mt-1 flex justify-between text-[10px] text-muted-foreground">
              <span>Bounce: 0.4%</span>
              <span>Spam: 0.01%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Middle Analytics Section: Bar Performance + Gauge / Health */}
      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Bar chart - 2 cols on lg */}
        <div className="rounded-xl border border-border/60 bg-background/60 p-4 lg:col-span-2">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Campaign Performance</h4>
              <p className="text-sm font-semibold text-foreground">Weekly Opens & Click-Throughs</p>
            </div>
            <span className="rounded-lg border border-border/70 px-2.5 py-1 text-xs font-medium text-muted-foreground">
              Last 7 days
            </span>
          </div>

          <div className="mt-6 flex h-40 items-end justify-between gap-2 sm:gap-4">
            {[
              { day: 'Mon', sends: 45, clicks: 28 },
              { day: 'Tue', sends: 60, clicks: 42 },
              { day: 'Wed', sends: 52, clicks: 36 },
              { day: 'Thu', sends: 92, clicks: 78, highlight: true },
              { day: 'Fri', sends: 74, clicks: 58 },
              { day: 'Sat', sends: 40, clicks: 25 },
              { day: 'Sun', sends: 35, clicks: 22 },
            ].map((col) => (
              <div key={col.day} className="flex flex-1 flex-col items-center gap-1.5">
                <div className="relative flex h-32 w-full items-end justify-center gap-1 sm:w-10">
                  <div
                    className={`w-3 sm:w-4 rounded-t transition-all ${
                      col.highlight ? 'bg-rose-500 shadow-md shadow-rose-500/30' : 'bg-rose-200 dark:bg-rose-950/60'
                    }`}
                    style={{ height: `${col.sends}%` }}
                  />
                  <div
                    className={`w-3 sm:w-4 rounded-t transition-all ${
                      col.highlight ? 'bg-pink-600' : 'bg-pink-300 dark:bg-pink-900/50'
                    }`}
                    style={{ height: `${col.clicks}%` }}
                  />
                </div>
                <span className="text-[11px] font-medium text-muted-foreground">{col.day}</span>
              </div>
            ))}
          </div>

          <div className="mt-3 flex items-center justify-center gap-6 border-t border-border/40 pt-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm bg-rose-500" /> Opens
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm bg-pink-300 dark:bg-pink-900/50" /> Clicks
            </span>
          </div>
        </div>

        {/* Gauge / Deliverability card */}
        <div className="flex flex-col justify-between rounded-xl border border-border/60 bg-background/60 p-4">
          <div>
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Deliverability Health</h4>
              <MoreHorizontal className="h-4 w-4 text-muted-foreground" />
            </div>
            <p className="mt-1 text-sm font-semibold text-foreground">Inbox Placement Gauge</p>
          </div>

          {/* SVG Semi-Circle Gauge */}
          <div className="relative mx-auto my-4 flex flex-col items-center justify-center">
            <svg viewBox="0 0 200 110" className="w-48 overflow-visible">
              <path
                d="M20,100 A80,80 0 0,1 180,100"
                fill="none"
                stroke="hsl(var(--muted))"
                strokeWidth="16"
                strokeLinecap="round"
              />
              <path
                d="M20,100 A80,80 0 0,1 180,100"
                fill="none"
                stroke="url(#roseGaugeGrad)"
                strokeWidth="16"
                strokeDasharray="251.2"
                strokeDashoffset="26"
                strokeLinecap="round"
              />
              <defs>
                <linearGradient id="roseGaugeGrad" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#f43f5e" />
                  <stop offset="100%" stopColor="#e11d48" />
                </linearGradient>
              </defs>
            </svg>
            <div className="absolute bottom-1 flex flex-col items-center">
              <span className="text-2xl font-extrabold text-foreground">99.2%</span>
              <span className="text-[11px] font-medium text-emerald-600 dark:text-emerald-400">Excellent Score</span>
            </div>
          </div>

          <div className="space-y-1.5 rounded-lg border border-border/40 bg-muted/30 p-2.5 text-xs">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> SPF &amp; DKIM
              </span>
              <span className="font-semibold text-emerald-600">Verified</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> DMARC Policy
              </span>
              <span className="font-semibold text-emerald-600">Enforced (p=reject)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
