import { TrendingUp, MousePointerClick } from 'lucide-react';

const linePath =
  'M20,250 C55,240 75,235 90,230 C110,238 125,248 140,245 C160,225 175,195 190,180 C210,188 225,200 240,195 C265,165 280,135 300,120 C325,132 345,148 360,140 C385,110 400,85 420,70 C435,60 448,52 460,45';

const areaPath = `${linePath} L460,278 L20,278 Z`;

export function GrowthChart() {
  return (
    <div className="relative">
      {/* Floating stat badges */}
      <div className="animate-float absolute -top-4 right-4 z-10 flex items-center gap-2 rounded-xl border border-border bg-card px-3 py-2 shadow-lg sm:right-10" style={{ animationDuration: '4s' }}>
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-green-500 to-emerald-500">
          <TrendingUp className="h-4 w-4 text-white" />
        </div>
        <div>
          <div className="text-sm font-bold leading-none">+180%</div>
          <div className="text-xs text-muted-foreground">Open Rate</div>
        </div>
      </div>
      <div className="animate-float absolute bottom-16 -left-2 z-10 flex items-center gap-2 rounded-xl border border-border bg-card px-3 py-2 shadow-lg sm:bottom-20 sm:-left-6" style={{ animationDuration: '4.5s', animationDelay: '0.6s' }}>
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500">
          <MousePointerClick className="h-4 w-4 text-white" />
        </div>
        <div>
          <div className="text-sm font-bold leading-none">3x</div>
          <div className="text-xs text-muted-foreground">Engagement</div>
        </div>
      </div>

      {/* Chart card */}
      <div className="rounded-3xl border border-border bg-card p-6 shadow-xl shadow-primary/5 sm:p-8">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <div className="text-sm font-medium text-muted-foreground">Campaign performance</div>
            <div className="text-2xl font-bold">Growing every month</div>
          </div>
          <div className="hidden items-center gap-1 rounded-full bg-green-500/10 px-3 py-1 text-sm font-medium text-green-600 dark:text-green-400 sm:flex">
            <TrendingUp className="h-4 w-4" />
            Trending up
          </div>
        </div>

        <svg viewBox="0 0 480 300" className="w-full overflow-visible" aria-hidden="true">
          <defs>
            <linearGradient id="growthFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="hsl(var(--primary) / 0.35)" />
              <stop offset="100%" stopColor="hsl(var(--primary) / 0)" />
            </linearGradient>
            <linearGradient id="growthLine" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="hsl(var(--gradient-from))" />
              <stop offset="100%" stopColor="hsl(var(--gradient-to))" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[70, 140, 210].map((y) => (
            <line key={y} x1="20" y1={y} x2="460" y2={y} stroke="hsl(var(--border))" strokeWidth="1" strokeDasharray="4 6" />
          ))}

          <path d={areaPath} fill="url(#growthFill)" stroke="none" />

          <path
            d={linePath}
            fill="none"
            stroke="url(#growthLine)"
            strokeWidth="4"
            strokeLinecap="round"
            pathLength="100"
            strokeDasharray="100"
          >
            <animate attributeName="stroke-dashoffset" values="100;0;0" keyTimes="0;0.7;1" dur="3.5s" repeatCount="indefinite" />
          </path>

          <circle r="7" fill="hsl(var(--background))" stroke="url(#growthLine)" strokeWidth="3">
            <animateMotion dur="3.5s" repeatCount="indefinite" path={linePath} keyPoints="0;1;1" keyTimes="0;0.7;1" calcMode="linear" />
          </circle>
        </svg>

        <div className="mt-2 flex justify-between text-xs text-muted-foreground">
          <span>6 months ago</span>
          <span>Today</span>
        </div>
      </div>
    </div>
  );
}
