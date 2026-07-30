'use client';

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  LabelList,
} from 'recharts';
import { chartAxisTick, chartColors, chartTooltipStyle } from './chart-theme';
import { ChartEmptyState } from './chart-empty-state';

interface EngagementFunnelChartProps {
  sent: number;
  delivered: number;
  opened: number;
  clicked: number;
}

export function EngagementFunnelChart({ sent, delivered, opened, clicked }: EngagementFunnelChartProps) {
  if (!sent) {
    return <ChartEmptyState message="Launch this campaign to see the engagement funnel" />;
  }

  const stages = [
    { stage: 'Sent', value: sent, color: chartColors.muted },
    { stage: 'Delivered', value: delivered, color: chartColors.chart1 },
    { stage: 'Opened', value: opened, color: chartColors.chart2 },
    { stage: 'Clicked', value: clicked, color: chartColors.chart3 },
  ].map((row) => ({ ...row, percentOfSent: sent > 0 ? Math.round((row.value / sent) * 1000) / 10 : 0 }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={stages} layout="vertical" margin={{ top: 4, right: 32, left: 8, bottom: 4 }} barCategoryGap="24%">
        <XAxis type="number" hide />
        <YAxis
          type="category"
          dataKey="stage"
          tick={chartAxisTick}
          tickLine={false}
          axisLine={false}
          width={72}
        />
        <Tooltip
          {...chartTooltipStyle}
          formatter={(value, _name, item) => [
            `${Number(value).toLocaleString()} (${(item.payload as { percentOfSent: number }).percentOfSent}% of sent)`,
            (item.payload as { stage: string }).stage,
          ]}
        />
        <Bar dataKey="value" radius={[0, 6, 6, 0]} maxBarSize={28}>
          {stages.map((row) => (
            <Cell key={row.stage} fill={row.color} />
          ))}
          <LabelList
            dataKey="value"
            position="right"
            style={{ fill: 'hsl(var(--foreground))', fontSize: 12, fontWeight: 600 }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
