'use client';

import { useCallback, useEffect, useState } from 'react';
import api from '@/config/axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
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
import { toast } from 'sonner';
import {
  Inbox,
  Send,
  RefreshCw,
  Plus,
  Mail,
  MailOpen,
  Star,
  Trash2,
  Reply,
  Paperclip,
  ArrowLeft,
} from 'lucide-react';
import type { AxiosError } from 'axios';

interface EmailAccount {
  id: string;
  name: string;
  email_address: string;
  account_type: 'GMAIL' | 'AWS_SES' | 'SENDGRID' | 'BREVO' | 'CUSTOM';
  display_name: string;
  sync_enabled: boolean;
  sync_status: string;
  last_synced_at: string | null;
  last_sync_error: string;
  is_default: boolean;
  unread_count: number;
}

interface MailboxMessage {
  id: string;
  account: string;
  account_email?: string;
  account_name?: string;
  direction: 'INBOUND' | 'OUTBOUND';
  folder: string;
  from_address: string;
  from_name: string;
  to_addresses: string[];
  cc_addresses?: string[];
  subject: string;
  snippet: string;
  text_body?: string;
  html_body?: string;
  is_read: boolean;
  is_starred: boolean;
  sent_at: string | null;
  received_at: string | null;
  has_attachments?: boolean;
  attachments_meta?: { filename?: string; content_type?: string; size?: number }[];
  thread_key?: string;
}

interface MailboxStats {
  accounts: number;
  inbox: number;
  unread: number;
  sent: number;
  drafts: number;
  trash: number;
}

function unwrapData<T>(payload: unknown): T {
  if (payload && typeof payload === 'object' && 'data' in payload) {
    return (payload as { data: T }).data;
  }
  return payload as T;
}

export default function InboxPage() {
  const [accounts, setAccounts] = useState<EmailAccount[]>([]);
  const [messages, setMessages] = useState<MailboxMessage[]>([]);
  const [stats, setStats] = useState<MailboxStats | null>(null);
  const [selected, setSelected] = useState<MailboxMessage | null>(null);
  const [folder, setFolder] = useState('INBOX');
  const [accountFilter, setAccountFilter] = useState<string>('all');
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);

  const [connectOpen, setConnectOpen] = useState(false);
  const [composeOpen, setComposeOpen] = useState(false);
  const [replyTo, setReplyTo] = useState<MailboxMessage | null>(null);

  const [connectForm, setConnectForm] = useState({
    name: '',
    email_address: '',
    account_type: 'GMAIL' as EmailAccount['account_type'],
    display_name: '',
    app_password: '',
    aws_access_key_id: '',
    aws_secret_access_key: '',
    region_name: 'us-east-1',
    configuration_set: '',
    api_key: '',
    smtp_server: '',
    smtp_port: '587',
    imap_server: '',
    imap_port: '993',
    password: '',
  });

  const [composeForm, setComposeForm] = useState({
    account_id: '',
    to: '',
    cc: '',
    subject: '',
    body: '',
  });

  const fetchAccounts = useCallback(async () => {
    try {
      const res = await api.get('/campaigns/mailbox/accounts/');
      const data = unwrapData<EmailAccount[]>(res.data);
      setAccounts(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error(error);
      toast.error('Failed to load mailbox accounts');
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const res = await api.get('/campaigns/mailbox/stats/');
      setStats(unwrapData<MailboxStats>(res.data));
    } catch (error) {
      console.error(error);
    }
  }, []);

  const fetchMessages = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('folder', folder);
      if (accountFilter !== 'all') params.set('account_id', accountFilter);
      if (search) params.set('q', search);
      const res = await api.get(`/campaigns/mailbox/messages/?${params.toString()}`);
      const data = unwrapData<{ results: MailboxMessage[] }>(res.data);
      setMessages(data?.results || []);
    } catch (error) {
      console.error(error);
      toast.error('Failed to load messages');
    } finally {
      setIsLoading(false);
    }
  }, [folder, accountFilter, search]);

  useEffect(() => {
    fetchAccounts();
    fetchStats();
  }, [fetchAccounts, fetchStats]);

  useEffect(() => {
    fetchMessages();
  }, [fetchMessages]);

  const openMessage = async (id: string) => {
    try {
      const res = await api.get(`/campaigns/mailbox/messages/${id}/`);
      const msg = unwrapData<MailboxMessage>(res.data);
      setSelected(msg);
      fetchMessages();
      fetchStats();
    } catch (error) {
      console.error(error);
      toast.error('Failed to open message');
    }
  };

  const handleSync = async (accountId?: string) => {
    const targets = accountId
      ? accounts.filter((a) => a.id === accountId)
      : accounts.filter((a) => !['AWS_SES', 'SENDGRID', 'BREVO'].includes(a.account_type));
    if (!targets.length) {
      toast.message('No IMAP accounts to sync (SES/SendGrid/Brevo use webhooks)');
      return;
    }
    setIsSyncing(true);
    try {
      for (const account of targets) {
        await api.post(`/campaigns/mailbox/accounts/${account.id}/sync/`);
      }
      toast.success('Mailbox synced');
      await fetchMessages();
      await fetchAccounts();
      await fetchStats();
    } catch (error) {
      const axiosError = error as AxiosError<{ message?: string }>;
      toast.error(axiosError.response?.data?.message || 'Sync failed');
    } finally {
      setIsSyncing(false);
    }
  };

  const handleConnect = async () => {
    try {
      let config: Record<string, unknown> = {};
      if (connectForm.account_type === 'GMAIL') {
        if (!connectForm.app_password) {
          toast.error('Gmail App Password is required');
          return;
        }
        config = {
          app_password: connectForm.app_password,
          password: connectForm.app_password,
          username: connectForm.email_address,
          from_email: connectForm.email_address,
        };
      } else if (connectForm.account_type === 'AWS_SES') {
        if (!connectForm.aws_access_key_id || !connectForm.aws_secret_access_key) {
          toast.error('AWS credentials are required');
          return;
        }
        config = {
          aws_access_key_id: connectForm.aws_access_key_id,
          aws_secret_access_key: connectForm.aws_secret_access_key,
          region_name: connectForm.region_name,
          configuration_set: connectForm.configuration_set || undefined,
          from_email: connectForm.email_address,
        };
      } else if (connectForm.account_type === 'SENDGRID' || connectForm.account_type === 'BREVO') {
        if (!connectForm.api_key) {
          toast.error('API key is required');
          return;
        }
        config = {
          api_key: connectForm.api_key,
          from_email: connectForm.email_address,
          enable_tracking: true,
        };
      } else {
        config = {
          smtp_server: connectForm.smtp_server,
          smtp_port: parseInt(connectForm.smtp_port || '587', 10),
          imap_server: connectForm.imap_server,
          imap_port: parseInt(connectForm.imap_port || '993', 10),
          username: connectForm.email_address,
          password: connectForm.password,
          from_email: connectForm.email_address,
          use_tls: true,
        };
      }

      await api.post('/campaigns/mailbox/accounts/', {
        name: connectForm.name || connectForm.email_address,
        email_address: connectForm.email_address,
        account_type: connectForm.account_type,
        display_name: connectForm.display_name,
        is_default: accounts.length === 0,
        config,
      });
      toast.success('Mailbox connected');
      setConnectOpen(false);
      fetchAccounts();
      fetchStats();
    } catch (error) {
      const axiosError = error as AxiosError<{ message?: string }>;
      toast.error(axiosError.response?.data?.message || 'Failed to connect account');
    }
  };

  const openCompose = (reply?: MailboxMessage | null) => {
    setReplyTo(reply || null);
    setComposeForm({
      account_id: reply?.account || accounts[0]?.id || '',
      to: reply ? reply.from_address : '',
      cc: '',
      subject: reply ? (reply.subject.startsWith('Re:') ? reply.subject : `Re: ${reply.subject}`) : '',
      body: '',
    });
    setComposeOpen(true);
  };

  const handleSend = async () => {
    if (!composeForm.account_id || !composeForm.to || !composeForm.subject) {
      toast.error('Account, recipient, and subject are required');
      return;
    }
    try {
      await api.post('/campaigns/mailbox/compose/', {
        account_id: composeForm.account_id,
        to: composeForm.to.split(',').map((s) => s.trim()).filter(Boolean),
        cc: composeForm.cc
          ? composeForm.cc.split(',').map((s) => s.trim()).filter(Boolean)
          : [],
        subject: composeForm.subject,
        text_body: composeForm.body,
        html_body: `<p>${composeForm.body.replace(/\n/g, '<br/>')}</p>`,
        reply_to_message_id: replyTo?.id || null,
      });
      toast.success('Message sent');
      setComposeOpen(false);
      setFolder('SENT');
      fetchMessages();
      fetchStats();
    } catch (error) {
      const axiosError = error as AxiosError<{ message?: string; data?: { error?: { message?: string } } }>;
      const msg =
        axiosError.response?.data?.message ||
        axiosError.response?.data?.data?.error?.message ||
        'Failed to send message';
      toast.error(msg);
    }
  };

  const toggleStar = async (msg: MailboxMessage) => {
    try {
      await api.patch(`/campaigns/mailbox/messages/${msg.id}/`, { is_starred: !msg.is_starred });
      fetchMessages();
      if (selected?.id === msg.id) {
        setSelected({ ...msg, is_starred: !msg.is_starred });
      }
    } catch {
      toast.error('Failed to update message');
    }
  };

  const moveToTrash = async (msg: MailboxMessage) => {
    try {
      await api.delete(`/campaigns/mailbox/messages/${msg.id}/`);
      toast.success('Moved to trash');
      setSelected(null);
      fetchMessages();
      fetchStats();
    } catch {
      toast.error('Failed to delete message');
    }
  };

  const formatDate = (value?: string | null) => {
    if (!value) return '';
    return new Date(value).toLocaleString();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Inbox</h2>
          <p className="text-muted-foreground">
            Send and receive mail with Gmail or AWS SES — just like a normal mailbox.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => handleSync()} disabled={isSyncing}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isSyncing ? 'animate-spin' : ''}`} />
            Sync
          </Button>
          <Button variant="outline" onClick={() => setConnectOpen(true)}>
            <Plus className="mr-2 h-4 w-4" /> Connect mailbox
          </Button>
          <Button onClick={() => openCompose()} disabled={!accounts.length}>
            <Send className="mr-2 h-4 w-4" /> Compose
          </Button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Unread</CardDescription>
            <CardTitle className="text-3xl">{stats?.unread ?? 0}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Inbox</CardDescription>
            <CardTitle className="text-3xl">{stats?.inbox ?? 0}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Sent</CardDescription>
            <CardTitle className="text-3xl">{stats?.sent ?? 0}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Connected accounts</CardDescription>
            <CardTitle className="text-3xl">{stats?.accounts ?? accounts.length}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {accounts.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {accounts.map((account) => (
            <Badge
              key={account.id}
              variant={accountFilter === account.id ? 'default' : 'outline'}
              className="cursor-pointer px-3 py-1"
              onClick={() => setAccountFilter(accountFilter === account.id ? 'all' : account.id)}
            >
                  {account.account_type === 'GMAIL'
                    ? 'Gmail'
                    : account.account_type === 'AWS_SES'
                      ? 'SES'
                      : account.account_type === 'SENDGRID'
                        ? 'SendGrid'
                        : account.account_type === 'BREVO'
                          ? 'Brevo'
                          : 'SMTP'}{' '}
                  · {account.email_address}
              {account.unread_count > 0 ? ` (${account.unread_count})` : ''}
            </Badge>
          ))}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
        <Card className="h-fit">
          <CardContent className="p-3 space-y-1">
            {[
              { id: 'INBOX', label: 'Inbox', icon: Inbox, count: stats?.inbox },
              { id: 'SENT', label: 'Sent', icon: Send, count: stats?.sent },
              { id: 'TRASH', label: 'Trash', icon: Trash2, count: stats?.trash },
            ].map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => {
                  setFolder(item.id);
                  setSelected(null);
                }}
                className={`flex w-full items-center justify-between rounded-md px-3 py-2 text-sm transition ${
                  folder === item.id ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
                }`}
              >
                <span className="flex items-center gap-2">
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </span>
                <span className="text-xs opacity-80">{item.count ?? 0}</span>
              </button>
            ))}
          </CardContent>
        </Card>

        <Card className="min-h-[480px]">
          <CardHeader className="pb-3">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <CardTitle className="text-lg">{folder === 'INBOX' ? 'Inbox' : folder === 'SENT' ? 'Sent' : 'Trash'}</CardTitle>
              <Input
                placeholder="Search mail..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="max-w-sm"
              />
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {!accounts.length ? (
              <div className="p-10 text-center text-muted-foreground">
                <Mail className="mx-auto mb-3 h-10 w-10 opacity-50" />
                <p className="font-medium">No mailbox connected</p>
                <p className="text-sm mt-1">Connect Gmail (App Password) or AWS SES to send and receive.</p>
                <Button className="mt-4" onClick={() => setConnectOpen(true)}>
                  Connect mailbox
                </Button>
              </div>
            ) : selected ? (
              <div className="border-t">
                <div className="flex items-center gap-2 border-b p-3">
                  <Button variant="ghost" size="icon" onClick={() => setSelected(null)}>
                    <ArrowLeft className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => openCompose(selected)}>
                    <Reply className="mr-2 h-4 w-4" /> Reply
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => toggleStar(selected)}>
                    <Star className={`h-4 w-4 ${selected.is_starred ? 'fill-yellow-400 text-yellow-400' : ''}`} />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => moveToTrash(selected)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
                <div className="space-y-4 p-6">
                  <div>
                    <h3 className="text-xl font-semibold">{selected.subject || '(no subject)'}</h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      {selected.from_name || selected.from_address} &lt;{selected.from_address}&gt;
                      {' · '}
                      {formatDate(selected.received_at || selected.sent_at)}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      To: {(selected.to_addresses || []).join(', ')}
                    </p>
                  </div>
                  {selected.html_body ? (
                    <div
                      className="prose prose-sm dark:prose-invert max-w-none border rounded-md p-4 bg-muted/30"
                      dangerouslySetInnerHTML={{ __html: selected.html_body }}
                    />
                  ) : (
                    <pre className="whitespace-pre-wrap text-sm border rounded-md p-4 bg-muted/30">
                      {selected.text_body || selected.snippet}
                    </pre>
                  )}
                </div>
              </div>
            ) : isLoading ? (
              <div className="p-10 text-center text-muted-foreground">Loading messages...</div>
            ) : messages.length === 0 ? (
              <div className="p-10 text-center text-muted-foreground">No messages in this folder.</div>
            ) : (
              <ul className="divide-y border-t">
                {messages.map((msg) => (
                  <li key={msg.id}>
                    <button
                      type="button"
                      className={`flex w-full items-start gap-3 px-4 py-3 text-left hover:bg-muted/60 ${
                        !msg.is_read ? 'bg-muted/30' : ''
                      }`}
                      onClick={() => openMessage(msg.id)}
                    >
                      <div className="mt-1">
                        {msg.is_read ? (
                          <MailOpen className="h-4 w-4 text-muted-foreground" />
                        ) : (
                          <Mail className="h-4 w-4 text-primary" />
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between gap-2">
                          <p className={`truncate text-sm ${!msg.is_read ? 'font-semibold' : ''}`}>
                            {folder === 'SENT'
                              ? (msg.to_addresses || []).join(', ')
                              : msg.from_name || msg.from_address}
                          </p>
                          <span className="shrink-0 text-xs text-muted-foreground">
                            {formatDate(msg.received_at || msg.sent_at)}
                          </span>
                        </div>
                        <p className={`truncate text-sm ${!msg.is_read ? 'font-medium' : 'text-muted-foreground'}`}>
                          {msg.subject || '(no subject)'}
                        </p>
                        <p className="truncate text-xs text-muted-foreground">{msg.snippet}</p>
                      </div>
                      {msg.has_attachments ? <Paperclip className="mt-1 h-4 w-4 text-muted-foreground" /> : null}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      <Dialog open={connectOpen} onOpenChange={setConnectOpen}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Connect mailbox</DialogTitle>
            <DialogDescription>
              Gmail uses SMTP + IMAP with an App Password. SES sends via API and receives via SNS inbound webhook.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Account type</Label>
              <Select
                value={connectForm.account_type}
                onValueChange={(val) =>
                  setConnectForm((f) => ({ ...f, account_type: val as EmailAccount['account_type'] }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="GMAIL">Gmail</SelectItem>
                  <SelectItem value="AWS_SES">Amazon SES</SelectItem>
                  <SelectItem value="SENDGRID">SendGrid</SelectItem>
                  <SelectItem value="BREVO">Brevo</SelectItem>
                  <SelectItem value="CUSTOM">Custom SMTP/IMAP</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Email address</Label>
              <Input
                value={connectForm.email_address}
                onChange={(e) => setConnectForm((f) => ({ ...f, email_address: e.target.value }))}
                placeholder="you@example.com"
              />
            </div>
            <div className="space-y-2">
              <Label>Display name</Label>
              <Input
                value={connectForm.display_name}
                onChange={(e) => setConnectForm((f) => ({ ...f, display_name: e.target.value }))}
                placeholder="Support Team"
              />
            </div>
            <div className="space-y-2">
              <Label>Account label</Label>
              <Input
                value={connectForm.name}
                onChange={(e) => setConnectForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="Work Gmail"
              />
            </div>

            {connectForm.account_type === 'GMAIL' && (
              <div className="space-y-2">
                <Label>App password</Label>
                <Input
                  type="password"
                  value={connectForm.app_password}
                  onChange={(e) => setConnectForm((f) => ({ ...f, app_password: e.target.value }))}
                  placeholder="16-character Google App Password"
                />
                <p className="text-xs text-muted-foreground">
                  Google Account → Security → 2-Step Verification → App passwords.
                </p>
              </div>
            )}

            {connectForm.account_type === 'AWS_SES' && (
              <>
                <div className="space-y-2">
                  <Label>AWS Access Key ID</Label>
                  <Input
                    value={connectForm.aws_access_key_id}
                    onChange={(e) => setConnectForm((f) => ({ ...f, aws_access_key_id: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label>AWS Secret Access Key</Label>
                  <Input
                    type="password"
                    value={connectForm.aws_secret_access_key}
                    onChange={(e) => setConnectForm((f) => ({ ...f, aws_secret_access_key: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Region</Label>
                  <Input
                    value={connectForm.region_name}
                    onChange={(e) => setConnectForm((f) => ({ ...f, region_name: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Configuration set (for opens/bounces)</Label>
                  <Input
                    value={connectForm.configuration_set}
                    onChange={(e) => setConnectForm((f) => ({ ...f, configuration_set: e.target.value }))}
                    placeholder="my-ses-config-set"
                  />
                  <p className="text-xs text-muted-foreground">
                    Point SNS to <code>/api/v1/campaigns/webhooks/ses/</code> for bounce/open/click/received events.
                  </p>
                </div>
              </>
            )}

            {(connectForm.account_type === 'SENDGRID' || connectForm.account_type === 'BREVO') && (
              <div className="space-y-2">
                <Label>API key</Label>
                <Input
                  type="password"
                  value={connectForm.api_key}
                  onChange={(e) => setConnectForm((f) => ({ ...f, api_key: e.target.value }))}
                  placeholder={connectForm.account_type === 'SENDGRID' ? 'SG....' : 'xkeysib-...'}
                />
                <p className="text-xs text-muted-foreground">
                  {connectForm.account_type === 'SENDGRID'
                    ? 'Event webhook → /api/v1/campaigns/webhooks/sendgrid/ · Inbound Parse → /webhooks/sendgrid/inbound/'
                    : 'Transactional webhook → /api/v1/campaigns/webhooks/brevo/'}
                </p>
              </div>
            )}

            {connectForm.account_type === 'CUSTOM' && (
              <>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <Label>SMTP server</Label>
                    <Input
                      value={connectForm.smtp_server}
                      onChange={(e) => setConnectForm((f) => ({ ...f, smtp_server: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>SMTP port</Label>
                    <Input
                      value={connectForm.smtp_port}
                      onChange={(e) => setConnectForm((f) => ({ ...f, smtp_port: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>IMAP server</Label>
                    <Input
                      value={connectForm.imap_server}
                      onChange={(e) => setConnectForm((f) => ({ ...f, imap_server: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>IMAP port</Label>
                    <Input
                      value={connectForm.imap_port}
                      onChange={(e) => setConnectForm((f) => ({ ...f, imap_port: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Password</Label>
                  <Input
                    type="password"
                    value={connectForm.password}
                    onChange={(e) => setConnectForm((f) => ({ ...f, password: e.target.value }))}
                  />
                </div>
              </>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConnectOpen(false)}>Cancel</Button>
            <Button onClick={handleConnect}>Connect</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={composeOpen} onOpenChange={setComposeOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{replyTo ? 'Reply' : 'Compose'}</DialogTitle>
            <DialogDescription>Send from a connected mailbox account.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>From account</Label>
              <Select
                value={composeForm.account_id}
                onValueChange={(val) => setComposeForm((f) => ({ ...f, account_id: val }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select account" />
                </SelectTrigger>
                <SelectContent>
                  {accounts.map((a) => (
                    <SelectItem key={a.id} value={a.id}>
                      {a.email_address}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>To</Label>
              <Input
                value={composeForm.to}
                onChange={(e) => setComposeForm((f) => ({ ...f, to: e.target.value }))}
                placeholder="recipient@example.com"
              />
            </div>
            <div className="space-y-2">
              <Label>Cc</Label>
              <Input
                value={composeForm.cc}
                onChange={(e) => setComposeForm((f) => ({ ...f, cc: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Subject</Label>
              <Input
                value={composeForm.subject}
                onChange={(e) => setComposeForm((f) => ({ ...f, subject: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>Message</Label>
              <Textarea
                rows={8}
                value={composeForm.body}
                onChange={(e) => setComposeForm((f) => ({ ...f, body: e.target.value }))}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setComposeOpen(false)}>Cancel</Button>
            <Button onClick={handleSend}>
              <Send className="mr-2 h-4 w-4" /> Send
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
