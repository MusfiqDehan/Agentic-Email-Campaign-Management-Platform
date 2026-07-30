'use client';

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { chartAxisTick, chartColors, chartTooltipStyle } from './chart-theme';
import { ChartEmptyState } from './chart-empty-state';

interface ProviderStat {
  provider: string | null;
  total: number;
  delivery_rate: number;
  bounce_rate: number;
  open_rate?: number;
  click_rate?: number;
}

interface ProviderPerformanceChartProps {
  data: ProviderStat[];
}

export function ProviderPerformanceChart({ data }: ProviderPerformanceChartProps) {
  if (!data || data.length === 0) {
    return <ChartEmptyState message="No provider data yet" />;
  }

  const chartData = data.map((stat) => ({
    provider: stat.provider || 'Unknown',
    'Delivery rate': stat.delivery_rate,
    'Open rate': stat.open_rate ?? 0,
    'Click rate': stat.click_rate ?? 0,
    'Bounce rate': stat.bounce_rate,
  }));

  return (
    <ResponsiveContainer width="100%" height={Math.max(220, chartData.length * 70)}>
      <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 24, left: 8, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={chartColors.border} horizontal={false} />
        <XAxis type="number" unit="%" domain={[0, 100]} tick={chartAxisTick} tickLine={false} axisLine={{ stroke: chartColors.border }} />
        <YAxis type="category" dataKey="provider" tick={chartAxisTick} tickLine={false} axisLine={false} width={100} />
        <Tooltip {...chartTooltipStyle} formatter={(value) => `${value}%`} />
        <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} iconType="circle" iconSize={8} />
        <Bar dataKey="Delivery rate" fill={chartColors.chart1} radius={[0, 4, 4, 0]} maxBarSize={14} />
        <Bar dataKey="Open rate" fill={chartColors.chart2} radius={[0, 4, 4, 0]} maxBarSize={14} />
        <Bar dataKey="Click rate" fill={chartColors.chart3} radius={[0, 4, 4, 0]} maxBarSize={14} />
        <Bar dataKey="Bounce rate" fill={chartColors.destructive} radius={[0, 4, 4, 0]} maxBarSize={14} />
      </BarChart>
    </ResponsiveContainer>
  );
}
