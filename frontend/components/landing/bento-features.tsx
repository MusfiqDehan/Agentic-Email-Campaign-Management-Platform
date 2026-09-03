'use client';

import { useState } from 'react';
import {
  Sparkles,
  Bot,
  Calendar,
  Clock,
  CheckCircle2,
  Search,
  TrendingUp,
  ChevronRight,
} from 'lucide-react';

export function BentoFeatures() {
  const [scheduleTime, setScheduleTime] = useState('10:00 AM (Optimal)');

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
      {/* 1. AI-Powered Lead Finder */}
      <div className="group relative flex flex-col justify-between overflow-hidden rounded-3xl border border-border/80 bg-card p-6 shadow-sm transition-all duration-300 hover:border-purple-500/50 hover:shadow-xl hover:shadow-purple-500/5 sm:p-8">
        <div>
          <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-50 text-purple-600 ring-8 ring-purple-50/50 dark:bg-purple-950/40 dark:text-purple-400 dark:ring-purple-950/30">
            <Search className="h-6 w-6" />
          </div>
          <h3 className="text-xl font-bold tracking-tight text-foreground sm:text-2xl">
            AI-powered lead finder
          </h3>
          <p className="mt-2 text-sm text-muted-foreground sm:text-base">
            Discover verified emails and enriched contact profiles across LinkedIn, domains, and CRM data in seconds.
          </p>
        </div>

        {/* Interactive Mockup Visual */}
        <div className="mt-8 rounded-2xl border border-border/70 bg-background/80 p-4 shadow-inner">
          <div className="flex items-center justify-between border-b border-border/50 pb-3">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
              <span className="text-xs font-semibold text-foreground">Enriched Lead Profile</span>
            </div>
            <span className="rounded-full bg-purple-100 px-2 py-0.5 text-[10px] font-bold text-purple-700 dark:bg-purple-950 dark:text-purple-300">
              99.8% Confidence
            </span>
          </div>

          <div className="mt-3 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-full bg-gradient-to-tr from-purple-600 to-indigo-500 text-sm font-bold text-white shadow-md">
              JD
            </div>
            <div className="flex-1 overflow-hidden">
              <div className="flex items-center gap-1.5">
                <span className="truncate text-sm font-bold text-foreground">Jordan Diaz</span>
                <CheckCircle2 className="h-3.5 w-3.5 text-purple-600 dark:text-purple-400" />
              </div>
              <p className="truncate text-xs text-muted-foreground">VP of Growth at SaaSify</p>
            </div>
          </div>

          <div className="mt-3 grid grid-cols-2 gap-2 text-[11px]">
            <div className="rounded-lg bg-muted/40 p-2">
              <span className="block text-muted-foreground">Work Email</span>
              <span className="font-semibold text-foreground">jordan@saasify.co</span>
            </div>
            <div className="rounded-lg bg-muted/40 p-2">
              <span className="block text-muted-foreground">Tech Stack</span>
              <span className="font-semibold text-foreground">SES, Next.js, Stripe</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Built-in Email Copywriting */}
      <div className="group relative flex flex-col justify-between overflow-hidden rounded-3xl border border-border/80 bg-card p-6 shadow-sm transition-all duration-300 hover:border-purple-500/50 hover:shadow-xl hover:shadow-purple-500/5 sm:p-8">
        <div>
          <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-50 text-purple-600 ring-8 ring-purple-50/50 dark:bg-purple-950/40 dark:text-purple-400 dark:ring-purple-950/30">
            <Bot className="h-6 w-6" />
          </div>
          <h3 className="text-xl font-bold tracking-tight text-foreground sm:text-2xl">
            Built-in email copywriting
          </h3>
          <p className="mt-2 text-sm text-muted-foreground sm:text-base">
            Draft high-converting cold pitches, personalized follow-ups, and newsletter sequences powered by fine-tuned AI.
          </p>
        </div>

        {/* Interactive Editor Prompt Simulation */}
        <div className="mt-8 rounded-2xl border border-border/70 bg-background/80 p-4 shadow-inner">
          <div className="flex items-center justify-between border-b border-border/50 pb-2.5 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5 font-medium text-foreground">
              <Sparkles className="h-3.5 w-3.5 text-purple-600" /> AI Suggestions: Subject Line
            </span>
            <span className="text-[10px] text-purple-600 dark:text-purple-400">High Open Rate Prediction</span>
          </div>

          <div className="mt-3 space-y-2">
            <div className="flex items-center justify-between rounded-xl border border-purple-200 bg-purple-50/50 p-2.5 text-xs text-foreground dark:border-purple-900/60 dark:bg-purple-950/30">
              <span className="font-medium">&ldquo;Quick idea for scaling &#123;&#123;company&#125;&#125;&rsquo;s outbound outreach&rdquo;</span>
              <span className="rounded bg-purple-600 px-1.5 py-0.5 text-[10px] font-bold text-white">68% open</span>
            </div>
            <div className="flex items-center justify-between rounded-xl border border-border/40 bg-muted/20 p-2.5 text-xs text-muted-foreground">
              <span>&ldquo;Hey &#123;&#123;first_name&#125;&#125;, saw your latest campaign release&rdquo;</span>
              <span className="text-[10px]">54% open</span>
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between pt-1 text-[11px] text-muted-foreground">
            <span>Tone: Conversational, executive</span>
            <button
              type="button"
              className="inline-flex items-center gap-1 font-semibold text-purple-600 hover:text-purple-700 dark:text-purple-400"
            >
              Insert into campaign <ChevronRight className="h-3 w-3" />
            </button>
          </div>
        </div>
      </div>

      {/* 3. Smart Scheduling */}
      <div className="group relative flex flex-col justify-between overflow-hidden rounded-3xl border border-border/80 bg-card p-6 shadow-sm transition-all duration-300 hover:border-purple-500/50 hover:shadow-xl hover:shadow-purple-500/5 sm:p-8">
        <div>
          <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-50 text-purple-600 ring-8 ring-purple-50/50 dark:bg-purple-950/40 dark:text-purple-400 dark:ring-purple-950/30">
            <Calendar className="h-6 w-6" />
          </div>
          <h3 className="text-xl font-bold tracking-tight text-foreground sm:text-2xl">
            Smart scheduling
          </h3>
          <p className="mt-2 text-sm text-muted-foreground sm:text-base">
            Deliver each email right when recipient mailboxes are most active, respecting individual time zones automatically.
          </p>
        </div>

        {/* Schedule Selector & Heatmap Visual */}
        <div className="mt-8 rounded-2xl border border-border/70 bg-background/80 p-4 shadow-inner">
          <div className="flex items-center justify-between border-b border-border/50 pb-3">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-purple-600" />
              <span className="text-xs font-semibold text-foreground">Timezone Optimization Engine</span>
            </div>
            <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
              Recipient Local Time
            </span>
          </div>

          {/* Quick Slot Buttons */}
          <div className="mt-3 flex flex-wrap gap-2">
            {[
              '09:00 AM (Early bird)',
              '10:00 AM (Optimal)',
              '02:15 PM (Post-lunch)',
              '04:30 PM (End of day)',
            ].map((slot) => (
              <button
                key={slot}
                type="button"
                onClick={() => setScheduleTime(slot)}
                className={`rounded-lg px-2.5 py-1.5 text-xs font-medium transition-all ${
                  scheduleTime === slot
                    ? 'bg-purple-600 text-white shadow-sm'
                    : 'bg-muted/50 text-muted-foreground hover:bg-muted hover:text-foreground'
                }`}
              >
                {slot}
              </button>
            ))}
          </div>

          {/* Hourly distribution bars */}
          <div className="mt-4">
            <div className="mb-1 flex justify-between text-[10px] text-muted-foreground">
              <span>8am</span>
              <span>10am (Peak engagement)</span>
              <span>2pm</span>
              <span>6pm</span>
            </div>
            <div className="flex h-10 items-end gap-1.5">
              {[25, 45, 95, 80, 60, 50, 75, 40, 20].map((val, i) => (
                <div
                  key={i}
                  className={`flex-1 rounded-t transition-all ${
                    i === 2 ? 'bg-purple-600 shadow-md shadow-purple-500/30' : 'bg-muted'
                  }`}
                  style={{ height: `${val}%` }}
                />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 4. Real-time Data Updates */}
      <div className="group relative flex flex-col justify-between overflow-hidden rounded-3xl border border-border/80 bg-card p-6 shadow-sm transition-all duration-300 hover:border-purple-500/50 hover:shadow-xl hover:shadow-purple-500/5 sm:p-8">
        <div>
          <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-50 text-purple-600 ring-8 ring-purple-50/50 dark:bg-purple-950/40 dark:text-purple-400 dark:ring-purple-950/30">
            <TrendingUp className="h-6 w-6" />
          </div>
          <h3 className="text-xl font-bold tracking-tight text-foreground sm:text-2xl">
            Real-time data updates
          </h3>
          <p className="mt-2 text-sm text-muted-foreground sm:text-base">
            Watch live deliverability, open tracking, unsubscribe logs, and click webhooks stream without page refreshing.
          </p>
        </div>

        {/* Live Table Simulation */}
        <div className="mt-8 rounded-2xl border border-border/70 bg-background/80 p-4 shadow-inner">
          <div className="flex items-center justify-between border-b border-border/50 pb-2 text-xs">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
              <span className="font-semibold text-foreground">WebSocket Dispatch Queue</span>
            </div>
            <span className="text-[11px] text-muted-foreground">35 sends/sec</span>
          </div>

          <div className="mt-2.5 overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="text-[10px] uppercase tracking-wider text-muted-foreground">
                  <th className="pb-1">Campaign</th>
                  <th className="pb-1">Status</th>
                  <th className="pb-1 text-right">Opens</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40 text-[11px]">
                <tr>
                  <td className="py-2 font-medium text-foreground">Product Launch Q3</td>
                  <td className="py-2">
                    <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-600 dark:bg-emerald-950/50 dark:text-emerald-400">
                      Delivered
                    </span>
                  </td>
                  <td className="py-2 text-right font-bold text-foreground">64.2%</td>
                </tr>
                <tr>
                  <td className="py-2 font-medium text-foreground">Weekly Digest #42</td>
                  <td className="py-2">
                    <span className="inline-flex items-center rounded-full bg-purple-50 px-2 py-0.5 text-[10px] font-semibold text-purple-600 dark:bg-purple-950/50 dark:text-purple-400">
                      Sending
                    </span>
                  </td>
                  <td className="py-2 text-right font-bold text-foreground">41.8%</td>
                </tr>
                <tr>
                  <td className="py-2 font-medium text-foreground">Re-engagement Run</td>
                  <td className="py-2">
                    <span className="inline-flex items-center rounded-full bg-indigo-50 px-2 py-0.5 text-[10px] font-semibold text-indigo-600 dark:bg-indigo-950/50 dark:text-indigo-400">
                      Queued
                    </span>
                  </td>
                  <td className="py-2 text-right font-medium text-muted-foreground">--</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="mt-3 grid grid-cols-3 gap-2 border-t border-border/40 pt-2 text-center text-[10px]">
            <div>
              <span className="block text-muted-foreground">Delivered</span>
              <span className="text-xs font-bold text-foreground">99.8%</span>
            </div>
            <div>
              <span className="block text-muted-foreground">Click Rate</span>
              <span className="text-xs font-bold text-foreground">22.4%</span>
            </div>
            <div>
              <span className="block text-muted-foreground">Bounces</span>
              <span className="text-xs font-bold text-emerald-600">0.2%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
