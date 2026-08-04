'use client';

import { useCallback, useEffect, useState } from 'react';
import { Globe, Loader2, PauseCircle, PlayCircle } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import type { SendingDomain } from '@/services/domains';
import { fetchAllDomains, reactivateDomain, suspendDomain } from '@/services/admin';
import { getApiErrorMessage } from '@/config/api-error';

const STATUSES = ['ALL', 'PENDING_DNS', 'PENDING_VERIFICATION', 'VERIFIED', 'FAILED', 'SUSPENDED'];

interface AdminDomain extends SendingDomain {
  organization_name?: string;
}

export default function AdminDomainsPage() {
  const [domains, setDomains] = useState<AdminDomain[]>([]);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const filters = statusFilter !== 'ALL' ? { status: statusFilter } : undefined;
      setDomains(await fetchAllDomains(filters));
    } catch {
      toast.error('Failed to load domains');
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSuspend = async (domain: AdminDomain) => {
    const reason = prompt(`Reason for suspending ${domain.domain}?`) ?? '';
    setBusyId(domain.id);
    try {
      await suspendDomain(domain.id, reason);
      toast.success(`${domain.domain} suspended`);
      await load();
    } catch (err: unknown) {
      toast.error(getApiErrorMessage(err, 'Failed to suspend domain'));
    } finally {
      setBusyId(null);
    }
  };

  const handleReactivate = async (domain: AdminDomain) => {
    setBusyId(domain.id);
    try {
      await reactivateDomain(domain.id);
      toast.success(`${domain.domain} reactivated`);
      await load();
    } catch (err: unknown) {
      toast.error(getApiErrorMessage(err, 'Failed to reactivate domain'));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Globe className="h-6 w-6" /> All Sending Domains
          </h1>
          <p className="text-muted-foreground">
            Cross-tenant view of every registered domain. Suspension blocks sends immediately.
          </p>
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[220px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STATUSES.map((s) => (
              <SelectItem key={s} value={s}>
                {s === 'ALL' ? 'All statuses' : s.replaceAll('_', ' ')}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Domains ({domains.length})</CardTitle>
          <CardDescription>Suspend a domain to stop all sending from it across campaigns and inbox.</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Domain</TableHead>
                  <TableHead>Organization</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Mode</TableHead>
                  <TableHead>Sender emails</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {domains.map((domain) => (
                  <TableRow key={domain.id}>
                    <TableCell className="font-medium">{domain.domain}</TableCell>
                    <TableCell>{domain.organization_name}</TableCell>
                    <TableCell>
                      <Badge variant={domain.status === 'VERIFIED' ? 'default' : domain.status === 'SUSPENDED' ? 'destructive' : 'secondary'}>
                        {domain.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">{domain.ownership_mode}</TableCell>
                    <TableCell>{domain.sender_email_count}</TableCell>
                    <TableCell>
                      {domain.status === 'SUSPENDED' ? (
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={busyId === domain.id}
                          onClick={() => handleReactivate(domain)}
                        >
                          <PlayCircle className="h-4 w-4 mr-1" /> Reactivate
                        </Button>
                      ) : (
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={busyId === domain.id}
                          onClick={() => handleSuspend(domain)}
                        >
                          <PauseCircle className="h-4 w-4 mr-1" /> Suspend
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
