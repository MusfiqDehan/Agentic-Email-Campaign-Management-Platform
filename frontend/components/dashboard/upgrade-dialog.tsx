'use client';

import { useEffect, useState } from 'react';
import { Check, Loader2, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useOrgAdmin } from '@/contexts/AuthContext';
import { getApiErrorMessage } from '@/config/api-error';
import {
  fetchPackageCatalog,
  upgradePackage,
  type Package,
  type PackageCatalog,
} from '@/services/packages';

const FEATURE_FLAGS: Array<{ key: keyof Package; label: string }> = [
  { key: 'custom_domain_allowed', label: 'Custom sending domains' },
  { key: 'org_owned_ses_allowed', label: 'Org-owned SES' },
  { key: 'advanced_analytics', label: 'Advanced analytics' },
  { key: 'priority_support', label: 'Priority support' },
  { key: 'bulk_email_allowed', label: 'Bulk email' },
  { key: 'ab_testing_allowed', label: 'A/B testing' },
];

function formatLimit(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'Unlimited';
  return value.toLocaleString();
}

interface UpgradeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  catalog: PackageCatalog | null;
  onCatalogChange: (catalog: PackageCatalog) => void;
}

export function UpgradeDialog({
  open,
  onOpenChange,
  catalog,
  onCatalogChange,
}: UpgradeDialogProps) {
  const isOrgAdmin = useOrgAdmin();
  const [upgradingId, setUpgradingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setLoading(true);
    fetchPackageCatalog()
      .then((data) => {
        if (!cancelled) onCatalogChange(data);
      })
      .catch((err) => {
        if (!cancelled) toast.error(getApiErrorMessage(err, 'Failed to load packages'));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, onCatalogChange]);

  const handleUpgrade = async (pkg: Package) => {
    if (!isOrgAdmin) {
      toast.error('Ask an organization admin to upgrade your plan.');
      return;
    }
    setUpgradingId(pkg.id);
    try {
      const result = await upgradePackage(pkg.id);
      onCatalogChange(result);
      toast.success(
        result.changed
          ? `Upgraded to ${result.current_package?.display_name ?? pkg.display_name}`
          : `You're already on ${pkg.display_name}`
      );
      onOpenChange(false);
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Upgrade failed'));
    } finally {
      setUpgradingId(null);
    }
  };

  const currentName =
    catalog?.current_package?.display_name
    ?? catalog?.plan_type
    ?? 'Free';
  const packages = catalog?.available_upgrades ?? [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            Upgrade your plan
          </DialogTitle>
          <DialogDescription>
            You are currently on <span className="font-medium text-foreground">{currentName}</span>.
            Choose a higher-tier package to unlock more sending volume and features.
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : packages.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No higher-tier packages are available to upgrade to right now.
          </p>
        ) : (
          <div className="grid max-h-[65vh] gap-4 overflow-y-auto pr-1 sm:grid-cols-2 lg:grid-cols-3">
            {packages.map((pkg) => {
              const features = FEATURE_FLAGS.filter((f) => pkg[f.key]);
              const isBusy = upgradingId === pkg.id;
              return (
                <div
                  key={pkg.id}
                  className="flex flex-col rounded-2xl border border-border bg-card p-4 shadow-sm"
                >
                  <div className="mb-3 flex items-start justify-between gap-2">
                    <div>
                      <h3 className="text-base font-semibold">{pkg.display_name}</h3>
                      <p className="text-xs text-muted-foreground">{pkg.name}</p>
                    </div>
                    <Badge variant="purple">Upgrade</Badge>
                  </div>
                  {pkg.description ? (
                    <p className="mb-3 text-xs text-muted-foreground">{pkg.description}</p>
                  ) : null}
                  <ul className="mb-4 space-y-1 text-xs text-muted-foreground">
                    <li>{formatLimit(pkg.contacts_limit)} contacts</li>
                    <li>{formatLimit(pkg.campaigns_per_month)} campaigns / month</li>
                    <li>{formatLimit(pkg.emails_per_day)} emails / day</li>
                    <li>{formatLimit(pkg.emails_per_month)} emails / month</li>
                    <li>{formatLimit(pkg.max_domains)} sending domains</li>
                    <li>{formatLimit(pkg.max_sender_emails)} sender emails</li>
                  </ul>
                  {features.length > 0 && (
                    <ul className="mb-4 space-y-1.5 text-xs">
                      {features.map((f) => (
                        <li key={f.key} className="flex items-center gap-1.5">
                          <Check className="h-3.5 w-3.5 text-primary" />
                          {f.label}
                        </li>
                      ))}
                    </ul>
                  )}
                  <Button
                    className="mt-auto w-full"
                    disabled={!!upgradingId || !isOrgAdmin}
                    onClick={() => handleUpgrade(pkg)}
                  >
                    {isBusy && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    {isOrgAdmin ? `Upgrade to ${pkg.display_name}` : 'Admin required'}
                  </Button>
                </div>
              );
            })}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
