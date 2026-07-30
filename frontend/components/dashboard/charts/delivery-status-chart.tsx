'use client';

import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';
import { chartColors, chartTooltipStyle } from './chart-theme';
import { ChartEmptyState } from './chart-empty-state';

interface DeliveryStatusChartProps {
  data: Record<string, { count: number; percentage: number }>;
}

const STATUS_COLORS: Record<string, string> = {
  DELIVERED: chartColors.success,
  SENT: chartColors.chart1,
  OPENED: chartColors.chart2,
  CLICKED: chartColors.chart3,
  QUEUED: chartColors.chart4,
  PENDING: chartColors.chart4,
  BOUNCED: chartColors.destructive,
  FAILED: chartColors.destructive,
  COMPLAINED: chartColors.chart5,
  UNSUBSCRIBED: chartColors.muted,
};

export function DeliveryStatusChart({ data }: DeliveryStatusChartProps) {
  const entries = Object.entries(data || {}).filter(([, stat]) => stat.count > 0);

  if (entries.length === 0) {
    return <ChartEmptyState message="No delivery data yet" />;
  }

  const chartData = entries.map(([status, stat]) => ({
    status,
    count: stat.count,
    percentage: stat.percentage,
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={chartData}
          dataKey="count"
          nameKey="status"
          innerRadius="55%"
          outerRadius="85%"
          paddingAngle={2}
          strokeWidth={0}
        >
          {chartData.map((entry) => (
            <Cell key={entry.status} fill={STATUS_COLORS[entry.status] || chartColors.muted} />
          ))}
        </Pie>
        <Tooltip
          {...chartTooltipStyle}
          formatter={(value, _name, item) => [
            `${Number(value).toLocaleString()} (${(item.payload as { percentage: number }).percentage}%)`,
            (item.payload as { status: string }).status,
          ]}
        />
        <Legend
          layout="horizontal"
          verticalAlign="bottom"
          align="center"
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: 12, paddingTop: 12 }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
