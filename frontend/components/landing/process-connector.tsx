export function ProcessConnector() {
  const path = 'M0,5 L300,5';
  return (
    <svg
      viewBox="0 0 300 10"
      preserveAspectRatio="none"
      className="h-3 w-full overflow-visible"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="connectorDot" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="hsl(var(--gradient-from))" />
          <stop offset="100%" stopColor="hsl(var(--gradient-to))" />
        </linearGradient>
      </defs>
      <path d={path} fill="none" stroke="hsl(var(--primary) / 0.25)" strokeWidth="2" strokeDasharray="1 9" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
      <circle r="4" fill="url(#connectorDot)">
        <animateMotion dur="2.2s" repeatCount="indefinite" path={path} />
        <animate attributeName="opacity" values="0;1;1;0" dur="2.2s" repeatCount="indefinite" />
      </circle>
    </svg>
  );
}
