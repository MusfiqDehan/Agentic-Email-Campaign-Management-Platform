'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  Globe,
  Plus,
  Trash2,
  RefreshCw,
  Copy,
  CheckCircle2,
  AlertTriangle,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useToast } from '@/components/ui/use-toast';
import {
  DnsRecord,
  DomainLimits,
  SendingDomain,
  deleteDomain,
  fetchDomains,
  registerDomain,
  verifyDomainNow,
} from '@/services/domains';
import { getApiErrorMessage } from '@/config/api-error';

const STATUS_STYLES: Record<string, { label: string; className: string }> = {
  VERIFIED: { label: 'Verified', className: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' },
  PENDING_DNS: { label: 'Pending DNS', className: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' },
  PENDING_VERIFICATION: { label: 'Verifying', className: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' },
  FAILED: { label: 'Failed', className: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' },
  SUSPENDED: { label: 'Suspended', className: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' },
  DISABLED: { label: 'Disabled', className: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200' },
};

function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] ?? { label: status, className: '' };
  return <Badge className={style.className}>{style.label}</Badge>;
}

function DnsRecordsTable({ records }: { records: DnsRecord[] }) {
  const { toast } = useToast();
  const copy = (value: string) => {
    navigator.clipboard.writeText(value);
    toast({ title: 'Copied to clipboard' });
  };
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Type</TableHead>
          <TableHead>Name / Host</TableHead>
          <TableHead>Value</TableHead>
          <TableHead>Purpose</TableHead>
          <TableHead />
        </TableRow>
      </TableHeader>
      <TableBody>
        {records.map((record, i) => (
          <TableRow key={i}>
            <TableCell className="font-mono">{record.type}</TableCell>
            <TableCell className="font-mono text-xs break-all max-w-[220px]">{record.name}</TableCell>
            <TableCell className="font-mono text-xs break-all max-w-[260px]">{record.value}</TableCell>
            <TableCell className="text-xs text-muted-foreground">{record.purpose}</TableCell>
            <TableCell>
              <Button variant="ghost" size="sm" onClick={() => copy(`${record.name} ${record.type} ${record.value}`)}>
                <Copy className="h-4 w-4" />
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

export default function DomainsPage() {
  const { toast } = useToast();
  const [domains, setDomains] = useState<SendingDomain[]>([]);
  const [limits, setLimits] = useState<DomainLimits | null>(null);
  const [loading, setLoading] = useState(true);
  const [addOpen, setAddOpen] = useState(false);
  const [newDomain, setNewDomain] = useState('');
  const [ownershipMode, setOwnershipMode] = useState<'PLATFORM' | 'ORG'>('PLATFORM');
  const [providerId, setProviderId] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [dnsDomain, setDnsDomain] = useState<SendingDomain | null>(null);
  const [verifyingId, setVerifyingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await fetchDomains();
      setDomains(data.domains);
      setLimits(data.limits);
    } catch {
      toast({ title: 'Failed to load domains', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    load();
  }, [load]);

  const handleAdd = async () => {
    if (!newDomain.trim()) return;
    setSubmitting(true);
    try {
      const created = await registerDomain({
        domain: newDomain.trim(),
        ownership_mode: ownershipMode,
        provider_id: ownershipMode === 'ORG' ? providerId || null : null,
      });
      toast({ title: 'Domain registered', description: 'Add the DNS records to verify it.' });
      setAddOpen(false);
      setNewDomain('');
      setDnsDomain(created);
      await load();
    } catch (err: unknown) {
      toast({
        title: 'Could not register domain',
        description: getApiErrorMessage(err, 'Unexpected error'),
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleVerify = async (domain: SendingDomain) => {
    setVerifyingId(domain.id);
    try {
      const result = await verifyDomainNow(domain.id);
      if (result.verified) {
        toast({ title: `${domain.domain} is verified!` });
      } else {
        toast({
          title: 'Not verified yet',
          description: 'DNS changes can take up to 48h to propagate. We also re-check automatically.',
        });
      }
      await load();
    } catch (err: unknown) {
      toast({
        title: 'Verification check failed',
        description: getApiErrorMessage(err, 'Try again in a minute.'),
        variant: 'destructive',
      });
    } finally {
      setVerifyingId(null);
    }
  };

  const handleDelete = async (domain: SendingDomain) => {
    if (!confirm(`Delete ${domain.domain}? Its sender emails will stop working.`)) return;
    try {
      await deleteDomain(domain.id);
      toast({ title: `${domain.domain} deleted` });
      await load();
    } catch (err: unknown) {
      toast({
        title: 'Could not delete domain',
        description: getApiErrorMessage(err, 'Unexpected error'),
        variant: 'destructive',
      });
    }
  };

  const atLimit =
    limits?.max_domains != null && limits.used >= limits.max_domains;

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Globe className="h-6 w-6" /> Sending Domains
          </h1>
          <p className="text-muted-foreground">
            Register your own domains to send and receive email from addresses you control.
            {limits && limits.max_domains != null && (
              <span className="ml-2 font-medium">
                {limits.used} of {limits.max_domains} used
              </span>
            )}
          </p>
        </div>
        <Button onClick={() => setAddOpen(true)} disabled={!limits?.feature_enabled || !limits?.custom_domain_allowed || atLimit}>
          <Plus className="h-4 w-4 mr-2" /> Add domain
        </Button>
      </div>

      {limits && !limits.feature_enabled && (
        <Card className="border-yellow-300">
          <CardContent className="py-4 flex items-center gap-2 text-sm">
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
            The sending-domains feature is currently disabled for your organization. Contact support.
          </CardContent>
        </Card>
      )}
      {limits && limits.feature_enabled && !limits.custom_domain_allowed && (
        <Card className="border-yellow-300">
          <CardContent className="py-4 flex items-center gap-2 text-sm">
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
            Your current package does not include custom sending domains. Upgrade to unlock this feature.
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Your domains</CardTitle>
          <CardDescription>
            Verified domains can host as many sender addresses as your package allows.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : domains.length === 0 ? (
            <p className="text-sm text-muted-foreground py-6 text-center">
              No domains yet. Add your first domain to start sending from your own addresses.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Domain</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Mode</TableHead>
                  <TableHead>Sender emails</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {domains.map((domain) => (
                  <TableRow key={domain.id}>
                    <TableCell className="font-medium">
                      {domain.domain}
                      {domain.verification_error && (
                        <p className="text-xs text-red-500 mt-1">{domain.verification_error}</p>
                      )}
                      {domain.status === 'SUSPENDED' && domain.suspension_reason && (
                        <p className="text-xs text-red-500 mt-1">{domain.suspension_reason}</p>
                      )}
                    </TableCell>
                    <TableCell><StatusBadge status={domain.status} /></TableCell>
                    <TableCell className="text-sm">
                      {domain.ownership_mode === 'PLATFORM' ? 'Platform-managed' : 'Own AWS account'}
                    </TableCell>
                    <TableCell>{domain.sender_email_count}</TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button variant="outline" size="sm" onClick={() => setDnsDomain(domain)}>
                          DNS records
                        </Button>
                        {domain.status !== 'VERIFIED' && domain.status !== 'SUSPENDED' && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleVerify(domain)}
                            disabled={verifyingId === domain.id}
                          >
                            {verifyingId === domain.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <RefreshCw className="h-4 w-4" />
                            )}
                            <span className="ml-1">Check</span>
                          </Button>
                        )}
                        {domain.status === 'VERIFIED' && (
                          <CheckCircle2 className="h-5 w-5 text-green-500 self-center ml-1" />
                        )}
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(domain)}>
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Add domain dialog */}
      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add a sending domain</DialogTitle>
            <DialogDescription>
              After registering, you&apos;ll get DNS records to add at your DNS provider.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="domain">Domain</Label>
              <Input
                id="domain"
                placeholder="mail.yourcompany.com or yourcompany.com"
                value={newDomain}
                onChange={(e) => setNewDomain(e.target.value)}
              />
            </div>
            {limits?.org_owned_ses_allowed && (
              <div className="space-y-2">
                <Label>Where should the domain be verified?</Label>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant={ownershipMode === 'PLATFORM' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setOwnershipMode('PLATFORM')}
                  >
                    Platform (recommended)
                  </Button>
                  <Button
                    type="button"
                    variant={ownershipMode === 'ORG' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setOwnershipMode('ORG')}
                  >
                    My own AWS SES account
                  </Button>
                </div>
                {ownershipMode === 'ORG' && (
                  <div>
                    <Label htmlFor="provider">AWS SES provider ID</Label>
                    <Input
                      id="provider"
                      placeholder="UUID of your connected AWS SES provider"
                      value={providerId}
                      onChange={(e) => setProviderId(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Note: receiving email is only supported for platform-managed domains.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddOpen(false)}>Cancel</Button>
            <Button onClick={handleAdd} disabled={submitting || !newDomain.trim()}>
              {submitting && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              Register domain
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* DNS records dialog */}
      <Dialog open={!!dnsDomain} onOpenChange={(open) => !open && setDnsDomain(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>DNS records for {dnsDomain?.domain}</DialogTitle>
            <DialogDescription>
              Add these records at your DNS provider. Verification usually completes within minutes
              after propagation, and we re-check automatically every 10 minutes.
            </DialogDescription>
          </DialogHeader>
          <div className="max-h-[50vh] overflow-auto">
            {dnsDomain && <DnsRecordsTable records={dnsDomain.dns_records} />}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDnsDomain(null)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
