'use client';

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { format } from 'date-fns';
import { chartAxisTick, chartColors, chartTooltipStyle } from './chart-theme';
import { ChartEmptyState } from './chart-empty-state';

export interface CampaignTimelinePoint {
  period: string;
  sent: number;
  delivered: number;
  opened: number;
  clicked: number;
  bounced: number;
}

interface CampaignTimelineChartProps {
  data: CampaignTimelinePoint[];
  granularity?: 'day' | 'hour';
}

const SERIES: Array<{ key: keyof Omit<CampaignTimelinePoint, 'period'>; label: string; color: string }> = [
  { key: 'sent', label: 'Sent', color: chartColors.muted },
  { key: 'delivered', label: 'Delivered', color: chartColors.chart1 },
  { key: 'opened', label: 'Opened', color: chartColors.chart2 },
  { key: 'clicked', label: 'Clicked', color: chartColors.chart3 },
  { key: 'bounced', label: 'Bounced', color: chartColors.destructive },
];

export function CampaignTimelineChart({ data, granularity = 'day' }: CampaignTimelineChartProps) {
  if (!data || data.length === 0) {
    return <ChartEmptyState message="No delivery activity recorded yet" />;
  }

  const dateFormat = granularity === 'hour' ? 'MMM d, HH:mm' : 'MMM d';
  const chartData = data.map((point) => ({
    ...point,
    label: format(new Date(point.period), dateFormat),
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={chartData} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={chartColors.border} vertical={false} />
        <XAxis dataKey="label" tick={chartAxisTick} tickLine={false} axisLine={{ stroke: chartColors.border }} />
        <YAxis allowDecimals={false} tick={chartAxisTick} tickLine={false} axisLine={false} width={48} />
        <Tooltip {...chartTooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} iconType="circle" iconSize={8} />
        {SERIES.map((series) => (
          <Line
            key={series.key}
            type="monotone"
            dataKey={series.key}
            name={series.label}
            stroke={series.color}
            strokeWidth={2}
            strokeDasharray={series.key === 'sent' ? '4 4' : undefined}
            dot={{ r: 2.5, strokeWidth: 0, fill: series.color }}
            activeDot={{ r: 4 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
