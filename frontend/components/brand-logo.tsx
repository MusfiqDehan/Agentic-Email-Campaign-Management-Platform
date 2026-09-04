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
    <span className={cn('inline-flex items-center gap-2.5', className)}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/logo.svg"
        alt={showWordmark ? '' : 'EmailCampaign by MusfiqDehan'}
        width={size}
        height={size}
        className="shrink-0 rounded-xl shadow-lg shadow-primary/20"
        {...(priority ? { fetchPriority: 'high' as const } : {})}
      />
      {showWordmark && (
        <span
          className={cn('flex flex-col justify-center leading-none', wordmarkClassName)}
        >
          <span className="font-brand text-[1em] font-extrabold tracking-tight">
            EmailCampaign
          </span>
          <span className="font-brand-by mt-[0.28em] text-[0.52em] font-normal italic leading-none tracking-wide text-current/65">
            by MusfiqDehan
          </span>
        </span>
      )}
    </span>
  );
}
