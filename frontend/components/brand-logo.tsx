import { cn } from '@/config/utils';

type BrandLogoProps = {
  className?: string;
  size?: number;
  showWordmark?: boolean;
  wordmarkClassName?: string;
  priority?: boolean;
};

export function BrandLogo({
  className,
  size = 36,
  showWordmark = true,
  wordmarkClassName,
  priority = false,
}: BrandLogoProps) {
  return (
    <span className={cn('inline-flex items-center gap-2.5 font-bold', className)}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/logo.svg"
        alt="EmailCampaign"
        width={size}
        height={size}
        className="rounded-xl shadow-lg shadow-primary/20"
        {...(priority ? { fetchPriority: 'high' as const } : {})}
      />
      {showWordmark && (
        <span className={cn('leading-none', wordmarkClassName)}>EmailCampaign</span>
      )}
    </span>
  );
}
