'use client';

import { useCallback, useEffect, useState } from 'react';
import { AtSign, Inbox, Loader2, Plus, Trash2 } from 'lucide-react';
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
import { useToast } from '@/components/ui/use-toast';
import { SendingDomain, fetchDomains } from '@/services/domains';
import {
  SenderEmail,
  createSenderEmail,
  deleteSenderEmail,
  fetchSenderEmails,
} from '@/services/sender-emails';
import { getApiErrorMessage } from '@/config/api-error';

export default function SenderEmailsPage() {
  const { toast } = useToast();
  const [senders, setSenders] = useState<SenderEmail[]>([]);
  const [limits, setLimits] = useState<{ max_sender_emails: number | null; used: number } | null>(null);
  const [verifiedDomains, setVerifiedDomains] = useState<SendingDomain[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [domainId, setDomainId] = useState('');
  const [localPart, setLocalPart] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    try {
      const [senderData, domainData] = await Promise.all([fetchSenderEmails(), fetchDomains()]);
      setSenders(senderData.sender_emails);
      setLimits(senderData.limits);
      setVerifiedDomains(domainData.domains.filter((d) => d.status === 'VERIFIED'));
    } catch {
      toast({ title: 'Failed to load sender emails', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    load();
  }, [load]);

  const handleCreate = async () => {
    if (!domainId || !localPart.trim()) return;
    setSubmitting(true);
    try {
      const created = await createSenderEmail({
        domain_id: domainId,
        local_part: localPart.trim(),
        display_name: displayName.trim(),
      });
      toast({
        title: `${created.email_address} created`,
        description: created.receiving_supported
          ? 'This address can send and receive email — check your Inbox.'
          : 'This address is send-only (org-owned SES domain).',
      });
      setCreateOpen(false);
      setLocalPart('');
      setDisplayName('');
      await load();
    } catch (err: unknown) {
      toast({
        title: 'Could not create sender email',
        description: getApiErrorMessage(err, 'Unexpected error'),
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (sender: SenderEmail) => {
    if (!confirm(`Delete ${sender.email_address}? Campaigns using it will fail to launch.`)) return;
    try {
      await deleteSenderEmail(sender.id);
      toast({ title: `${sender.email_address} deleted` });
      await load();
    } catch (err: unknown) {
      toast({
        title: 'Could not delete sender email',
        description: getApiErrorMessage(err, 'Unexpected error'),
        variant: 'destructive',
      });
    }
  };

  const atLimit = limits?.max_sender_emails != null && limits.used >= limits.max_sender_emails;

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <AtSign className="h-6 w-6" /> Sender Emails
          </h1>
          <p className="text-muted-foreground">
            Create addresses on your verified domains for campaigns and your inbox.
            {limits && limits.max_sender_emails != null && (
              <span className="ml-2 font-medium">
                {limits.used} of {limits.max_sender_emails} used
              </span>
            )}
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)} disabled={verifiedDomains.length === 0 || atLimit}>
          <Plus className="h-4 w-4 mr-2" /> New sender email
        </Button>
      </div>

      {verifiedDomains.length === 0 && !loading && (
        <Card className="border-yellow-300">
          <CardContent className="py-4 text-sm">
            You need at least one <a className="underline" href="/dashboard/domains">verified sending domain</a>{' '}
            before creating sender emails.
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Your sender addresses</CardTitle>
          <CardDescription>
            Addresses on platform-managed domains also receive replies into your Inbox.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : senders.length === 0 ? (
            <p className="text-sm text-muted-foreground py-6 text-center">No sender emails yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Address</TableHead>
                  <TableHead>Display name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Receiving</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {senders.map((sender) => (
                  <TableRow key={sender.id}>
                    <TableCell className="font-medium">{sender.email_address}</TableCell>
                    <TableCell>{sender.display_name || '—'}</TableCell>
                    <TableCell>
                      {sender.status === 'ACTIVE' ? (
                        sender.is_usable ? (
                          <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">Active</Badge>
                        ) : (
                          <Badge className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">Domain unavailable</Badge>
                        )
                      ) : (
                        <Badge className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">Suspended</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {sender.receiving_supported ? (
                        <span className="flex items-center gap-1 text-sm text-muted-foreground">
                          <Inbox className="h-4 w-4" /> Inbox
                        </span>
                      ) : (
                        <span className="text-sm text-muted-foreground">Send-only</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm" onClick={() => handleDelete(sender)}>
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New sender email</DialogTitle>
            <DialogDescription>Create an address on one of your verified domains.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Domain</Label>
              <Select value={domainId} onValueChange={setDomainId}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a verified domain" />
                </SelectTrigger>
                <SelectContent>
                  {verifiedDomains.map((d) => (
                    <SelectItem key={d.id} value={d.id}>
                      {d.domain}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="localPart">Address</Label>
              <div className="flex items-center gap-1">
                <Input
                  id="localPart"
                  placeholder="support"
                  value={localPart}
                  onChange={(e) => setLocalPart(e.target.value)}
                />
                <span className="text-muted-foreground whitespace-nowrap">
                  @{verifiedDomains.find((d) => d.id === domainId)?.domain || 'domain'}
                </span>
              </div>
            </div>
            <div>
              <Label htmlFor="displayName">Display name (optional)</Label>
              <Input
                id="displayName"
                placeholder="Acme Support"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={submitting || !domainId || !localPart.trim()}>
              {submitting && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
