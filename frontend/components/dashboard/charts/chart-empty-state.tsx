import { LucideIcon, BarChart3 } from 'lucide-react';

interface ChartEmptyStateProps {
  message?: string;
  icon?: LucideIcon;
  height?: number;
}

export function ChartEmptyState({ message = 'No data yet', icon: Icon = BarChart3, height = 260 }: ChartEmptyStateProps) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-2 text-muted-foreground"
      style={{ height }}
    >
      <Icon className="h-8 w-8 opacity-30" />
      <p className="text-sm">{message}</p>
    </div>
  );
}
