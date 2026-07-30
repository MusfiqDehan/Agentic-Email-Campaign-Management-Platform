export const chartColors = {
  chart1: 'hsl(var(--chart-1))',
  chart2: 'hsl(var(--chart-2))',
  chart3: 'hsl(var(--chart-3))',
  chart4: 'hsl(var(--chart-4))',
  chart5: 'hsl(var(--chart-5))',
  muted: 'hsl(var(--muted-foreground))',
  border: 'hsl(var(--border))',
  destructive: 'hsl(var(--destructive))',
  success: 'hsl(var(--success))',
};

export const chartTooltipStyle = {
  contentStyle: {
    backgroundColor: 'hsl(var(--card))',
    border: '1px solid hsl(var(--border))',
    borderRadius: '0.75rem',
    boxShadow: '0 4px 12px hsl(var(--foreground) / 0.08)',
    color: 'hsl(var(--card-foreground))',
    fontSize: '0.8125rem',
    padding: '0.625rem 0.875rem',
  },
  labelStyle: {
    color: 'hsl(var(--muted-foreground))',
    fontWeight: 500,
    marginBottom: '0.25rem',
  },
  cursor: { fill: 'hsl(var(--muted) / 0.4)' },
};

export const chartAxisTick = { fill: 'hsl(var(--muted-foreground))', fontSize: 12 };
