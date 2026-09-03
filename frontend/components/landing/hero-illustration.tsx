'use client';

import { useRef } from 'react';
import { Mail, BarChart3, Shield, Users, Sparkles } from 'lucide-react';

const nodes = [
  { icon: Mail, label: 'Delivered', color: 'from-blue-500 to-cyan-500', left: '14%', top: '16%', path: 'M90,90 Q170,150 250,250', delay: '0s' },
  { icon: BarChart3, label: 'Opened', color: 'from-purple-500 to-indigo-500', left: '84%', top: '20%', path: 'M420,100 Q330,160 250,250', delay: '0.75s' },
  { icon: Shield, label: 'Secure', color: 'from-green-500 to-emerald-500', left: '16%', top: '82%', path: 'M100,410 Q170,340 250,250', delay: '1.5s' },
  { icon: Users, label: 'Engaged', color: 'from-orange-500 to-amber-500', left: '86%', top: '84%', path: 'M420,410 Q340,340 250,250', delay: '2.25s' },
];

export function HeroIllustration() {
  const tiltRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const el = tiltRef.current;
    if (!el) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    el.style.transform = `perspective(1000px) rotateY(${x * 10}deg) rotateX(${-y * 10}deg) scale(1.02)`;
  };

  const handleMouseLeave = () => {
    const el = tiltRef.current;
    if (!el) return;
    el.style.transform = 'perspective(1000px) rotateY(0deg) rotateX(0deg) scale(1)';
  };

  return (
    <div
      className="relative mx-auto aspect-square w-full max-w-md select-none sm:max-w-lg"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <div
        ref={tiltRef}
        className="relative h-full w-full transition-transform duration-300 ease-out will-change-transform"
      >
        {/* Ambient glow */}
        <div className="absolute left-1/2 top-1/2 h-[70%] w-[70%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/20 blur-[80px]" />

        {/* Animated connectors */}
        <svg
          viewBox="0 0 500 500"
          className="absolute inset-0 h-full w-full overflow-visible"
          aria-hidden="true"
        >
          <defs>
            <linearGradient id="dotGrad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="hsl(var(--gradient-from))" />
              <stop offset="100%" stopColor="hsl(var(--gradient-to))" />
            </linearGradient>
          </defs>

          {/* Dashed orbit ring */}
          <circle
            cx="250"
            cy="250"
            r="190"
            fill="none"
            stroke="hsl(var(--primary) / 0.15)"
            strokeWidth="1.5"
            strokeDasharray="2 10"
            className="origin-center animate-spin-slow"
          />

          {/* Connection paths + traveling packets */}
          {nodes.map((node, i) => (
            <g key={i}>
              <path
                d={node.path}
                fill="none"
                stroke="hsl(var(--primary) / 0.18)"
                strokeWidth="1.5"
                strokeDasharray="4 6"
              />
              <circle r="5" fill="url(#dotGrad)">
                <animateMotion dur="3s" repeatCount="indefinite" path={node.path} begin={node.delay} />
                <animate attributeName="opacity" values="0;1;1;0" dur="3s" repeatCount="indefinite" begin={node.delay} />
              </circle>
            </g>
          ))}
        </svg>

        {/* Floating feature badges */}
        {nodes.map((node, i) => (
          <div
            key={i}
            className="animate-float absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-1.5"
            style={{ left: node.left, top: node.top, animationDelay: `${i * 0.4}s`, animationDuration: `${3.5 + i * 0.4}s` }}
          >
            <div className={`flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br ${node.color} shadow-lg ring-4 ring-background`}>
              <node.icon className="h-6 w-6 text-white" />
            </div>
            <span className="rounded-full bg-card px-2.5 py-0.5 text-xs font-medium text-muted-foreground shadow-sm ring-1 ring-border">
              {node.label}
            </span>
          </div>
        ))}

        {/* Central card */}
        <div className="absolute left-1/2 top-1/2 flex h-40 w-40 -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center gap-2 rounded-3xl gradient-bg text-white shadow-2xl shadow-primary/30 animate-pulse-glow sm:h-48 sm:w-48">
          <Mail className="h-10 w-10" />
          <div className="flex items-end gap-1">
            {[8, 14, 10, 18, 12].map((h, i) => (
              <span
                key={i}
                className="w-1.5 rounded-full bg-white/70"
                style={{ height: `${h}px`, animation: `float ${1.2 + i * 0.15}s ease-in-out infinite alternate` }}
              />
            ))}
          </div>
          <div className="flex items-center gap-1 text-xs font-medium text-white/80">
            <Sparkles className="h-3 w-3" />
            <span>Sending campaigns</span>
          </div>
        </div>
      </div>
    </div>
  );
}
