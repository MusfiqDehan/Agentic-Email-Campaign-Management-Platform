const links = [
  { path: 'M40,60 C160,20 260,120 400,50', delay: '0s' },
  { path: 'M20,180 C140,140 240,220 380,160', delay: '0.9s' },
  { path: 'M60,300 C180,260 280,340 420,280', delay: '1.8s' },
  { path: 'M100,20 C200,90 300,10 380,90', delay: '2.7s' },
];

const dots = [
  { cx: 40, cy: 60 }, { cx: 400, cy: 50 },
  { cx: 20, cy: 180 }, { cx: 380, cy: 160 },
  { cx: 60, cy: 300 }, { cx: 420, cy: 280 },
  { cx: 100, cy: 20 }, { cx: 380, cy: 90 },
];

export function NetworkBackground() {
  return (
    <svg
      viewBox="0 0 440 340"
      preserveAspectRatio="none"
      className="absolute inset-0 h-full w-full opacity-70"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="networkDot" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="hsl(var(--gradient-from))" />
          <stop offset="100%" stopColor="hsl(var(--gradient-to))" />
        </linearGradient>
      </defs>

      {links.map((link, i) => (
        <g key={i}>
          <path d={link.path} fill="none" stroke="hsl(var(--primary) / 0.4)" strokeWidth="1.5" strokeDasharray="3 7" vectorEffect="non-scaling-stroke" />
          <circle r="4" fill="url(#networkDot)">
            <animateMotion dur="4s" repeatCount="indefinite" path={link.path} begin={link.delay} />
            <animate attributeName="opacity" values="0;1;1;0" dur="4s" repeatCount="indefinite" begin={link.delay} />
          </circle>
        </g>
      ))}

      {dots.map((dot, i) => (
        <circle key={i} cx={dot.cx} cy={dot.cy} r="3.5" fill="hsl(var(--primary) / 0.55)">
          <animate attributeName="r" values="3.5;5;3.5" dur="2.5s" repeatCount="indefinite" begin={`${i * 0.3}s`} />
        </circle>
      ))}
    </svg>
  );
}
