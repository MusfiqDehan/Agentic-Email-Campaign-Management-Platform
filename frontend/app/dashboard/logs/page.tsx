'use client';

import { useEffect, useState, useCallback } from 'react';
import api from '@/config/axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Search,
  Filter,
  MoreHorizontal,
  Eye,
  RefreshCw,
  Forward,
  Mail,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  TrendingUp,
  MousePointerClick,
  ChevronLeft,
  ChevronRight,
  Calendar,
  BarChart3,
  Send
} from 'lucide-react';
import { toast } from 'sonner';
import { Input } from '@/components/ui/input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

interface EmailDeliveryLog {
  id: string;
  recipient_email: string;
  sender_email: string;
  subject: string;
  delivery_status: string;
  sent_at: string | null;
  delivered_at: string | null;
  opened_at: string | null;
  clicked_at: string | null;
  bounced_at: string | null;
  open_count: number;
  click_count: number;
  bounce_type: string | null;
  bounce_reason: string | null;
  error_message: string | null;
  provider_name: string | null;
  trigger_type: string | null;
  automation_rule_name: string | null;
  email_template_body?: string;
  email_template_text_body?: string;
  created_at: string;
}

interface Analytics {
  total_emails: number;
  delivery_rates: Record<string, { count: number; percentage: number }>;
  engagement_rates: {
    open_rate: number;
    click_rate: number;
  };
  provider_stats: Array<{
    provider: string;
    total: number;
    delivery_rate: number;
    bounce_rate: number;
  }>;
}

interface PaginatedResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: EmailDeliveryLog[];
}

export default function DeliveryLogsPage() {
  const [logs, setLogs] = useState<EmailDeliveryLog[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyticsLoading, setIsAnalyticsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize] = useState(10);
  
  // Modal states
  const [selectedLog, setSelectedLog] = useState<EmailDeliveryLog | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [isForwardModalOpen, setIsForwardModalOpen] = useState(false);
  const [forwardEmail, setForwardEmail] = useState('');
  const [forwardReason, setForwardReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchLogs = useCallback(async (page: number = 1) => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', page.toString());
      params.append('page_size', pageSize.toString());
      
      if (searchQuery) {
        params.append('search', searchQuery);
      }
      if (statusFilter && statusFilter !== 'all') {
        params.append('delivery_status', statusFilter);
      }

      const response = await api.get(`/campaigns/logs/?${params.toString()}`);
      const data = response.data;
      
      // Handle paginated response
      if (data.results) {
        setLogs(data.results);
        setTotalCount(data.count);
      } else if (data.data?.results) {
        setLogs(data.data.results);
        setTotalCount(data.data.count);
      } else if (Array.isArray(data.data)) {
        setLogs(data.data);
        setTotalCount(data.data.length);
      } else if (Array.isArray(data)) {
        setLogs(data);
        setTotalCount(data.length);
      } else {
        setLogs([]);
        setTotalCount(0);
      }
    } catch (error) {
      console.error(error);
      toast.error('Failed to fetch delivery logs');
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, statusFilter, pageSize]);

  const fetchAnalytics = useCallback(async () => {
    setIsAnalyticsLoading(true);
    try {
      const response = await api.get('/campaigns/logs/analytics/');
      const data = response.data.data || response.data;
      setAnalytics(data);
    } catch (error) {
      console.error(error);
      toast.error('Failed to fetch analytics');
    } finally {
      setIsAnalyticsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLogs(currentPage);
  }, [fetchLogs, currentPage]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, statusFilter]);

  const fetchLogDetail = async (logId: string) => {
    try {
      const response = await api.get(`/campaigns/logs/${logId}/`);
      const data = response.data.data || response.data;
      setSelectedLog(data);
      setIsDetailModalOpen(true);
    } catch (error) {
      console.error(error);
      toast.error('Failed to fetch log details');
    }
  };

  const handleResend = async (logId: string) => {
    try {
      setIsSubmitting(true);
      await api.post(`/campaigns/logs/${logId}/resend/`, {
        reason: 'Manual resend from dashboard'
      });
      toast.success('Email queued for resend');
      fetchLogs(currentPage);
    } catch (error: any) {
      console.error(error);
      toast.error(error.response?.data?.message || 'Failed to resend email');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleForward = async () => {
    if (!selectedLog || !forwardEmail) return;
    
    try {
      setIsSubmitting(true);
      await api.post(`/campaigns/logs/${selectedLog.id}/forward/`, {
        new_recipient: forwardEmail,
        reason: forwardReason || 'Manual forward from dashboard'
      });
      toast.success('Email queued for forwarding');
      setIsForwardModalOpen(false);
      setForwardEmail('');
      setForwardReason('');
      setSelectedLog(null);
      fetchLogs(currentPage);
    } catch (error: any) {
      console.error(error);
      toast.error(error.response?.data?.message || 'Failed to forward email');
    } finally {
      setIsSubmitting(false);
    }
  };

  const openForwardModal = (log: EmailDeliveryLog) => {
    setSelectedLog(log);
    setIsForwardModalOpen(true);
  };

  const getStatusVariant = (status: string): "default" | "secondary" | "destructive" | "outline" | "success" | "info" | "warning" | "purple" => {
    switch (status) {
      case 'DELIVERED': return 'success';
      case 'SENT': return 'info';
      case 'PENDING': return 'warning';
      case 'QUEUED': return 'secondary';
      case 'FAILED': return 'destructive';
      case 'BOUNCED': return 'destructive';
      case 'OPENED': return 'purple';
      case 'CLICKED': return 'purple';
      default: return 'secondary';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'DELIVERED': return <CheckCircle className="h-4 w-4" />;
      case 'SENT': return <Send className="h-4 w-4" />;
      case 'PENDING': return <Clock className="h-4 w-4" />;
      case 'QUEUED': return <Clock className="h-4 w-4" />;
      case 'FAILED': return <XCircle className="h-4 w-4" />;
      case 'BOUNCED': return <AlertTriangle className="h-4 w-4" />;
      default: return <Mail className="h-4 w-4" />;
    }
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="space-y-6 sm:space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">Delivery Logs</h2>
          <p className="mt-1 text-muted-foreground">
            Track and manage your email deliveries
          </p>
        </div>
        <Button 
          variant="outline" 
          onClick={() => { fetchLogs(currentPage); fetchAnalytics(); }}
          className="w-full sm:w-auto"
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Analytics Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Emails</CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isAnalyticsLoading ? '...' : analytics?.total_emails?.toLocaleString() || 0}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Delivered</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {isAnalyticsLoading ? '...' : 
                `${analytics?.delivery_rates?.DELIVERED?.percentage || 0}%`}
            </div>
            <p className="text-xs text-muted-foreground">
              {analytics?.delivery_rates?.DELIVERED?.count || 0} emails
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Open Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {isAnalyticsLoading ? '...' : `${analytics?.engagement_rates?.open_rate || 0}%`}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Click Rate</CardTitle>
            <MousePointerClick className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              {isAnalyticsLoading ? '...' : `${analytics?.engagement_rates?.click_rate || 0}%`}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Provider Stats */}
      {analytics?.provider_stats && analytics.provider_stats.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Provider Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {analytics.provider_stats.map((stat) => (
                <div key={stat.provider} className="rounded-lg border p-4">
                  <div className="font-medium">{stat.provider || 'Unknown'}</div>
                  <div className="mt-2 space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Total</span>
                      <span className="font-medium">{stat.total}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Delivery Rate</span>
                      <span className="font-medium text-green-600">{stat.delivery_rate}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Bounce Rate</span>
                      <span className="font-medium text-red-600">{stat.bounce_rate}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search and Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by email, subject..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <Filter className="mr-2 h-4 w-4" />
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="DELIVERED">Delivered</SelectItem>
            <SelectItem value="SENT">Sent</SelectItem>
            <SelectItem value="PENDING">Pending</SelectItem>
            <SelectItem value="QUEUED">Queued</SelectItem>
            <SelectItem value="FAILED">Failed</SelectItem>
            <SelectItem value="BOUNCED">Bounced</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Logs Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <p className="mt-2 text-muted-foreground">Loading logs...</p>
            </div>
          ) : logs.length === 0 ? (
            <div className="p-8 text-center">
              <Mail className="mx-auto h-12 w-12 text-muted-foreground/50" />
              <h3 className="mt-4 font-semibold">No delivery logs found</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                {searchQuery || statusFilter !== 'all' 
                  ? 'Try adjusting your filters'
                  : 'Email delivery logs will appear here'}
              </p>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Recipient</TableHead>
                    <TableHead className="hidden md:table-cell">Subject</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="hidden lg:table-cell">Sent At</TableHead>
                    <TableHead className="hidden xl:table-cell">Opens</TableHead>
                    <TableHead className="hidden xl:table-cell">Clicks</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {logs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell>
                        <div className="font-medium truncate max-w-[200px]">{log.recipient_email}</div>
                        <div className="text-xs text-muted-foreground md:hidden truncate">
                          {log.subject}
                        </div>
                      </TableCell>
                      <TableCell className="hidden md:table-cell">
                        <div className="truncate max-w-[300px]">{log.subject}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusVariant(log.delivery_status)} className="gap-1">
                          {getStatusIcon(log.delivery_status)}
                          {log.delivery_status}
                        </Badge>
                      </TableCell>
                      <TableCell className="hidden lg:table-cell">
                        <div className="flex items-center gap-1 text-sm text-muted-foreground">
                          <Calendar className="h-3 w-3" />
                          {formatDate(log.sent_at)}
                        </div>
                      </TableCell>
                      <TableCell className="hidden xl:table-cell">
                        <span className="font-medium">{log.open_count}</span>
                      </TableCell>
                      <TableCell className="hidden xl:table-cell">
                        <span className="font-medium">{log.click_count}</span>
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => fetchLogDetail(log.id)}>
                              <Eye className="mr-2 h-4 w-4" />
                              View Details
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            {(log.delivery_status === 'FAILED' || log.delivery_status === 'BOUNCED') && (
                              <DropdownMenuItem 
                                onClick={() => handleResend(log.id)}
                                disabled={isSubmitting}
                              >
                                <RefreshCw className="mr-2 h-4 w-4" />
                                Resend Email
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuItem onClick={() => openForwardModal(log)}>
                              <Forward className="mr-2 h-4 w-4" />
                              Forward Email
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between border-t px-4 py-3">
                  <div className="text-sm text-muted-foreground">
                    Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} logs
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                      Previous
                    </Button>
                    <div className="flex items-center gap-1">
                      {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                        let pageNum;
                        if (totalPages <= 5) {
                          pageNum = i + 1;
                        } else if (currentPage <= 3) {
                          pageNum = i + 1;
                        } else if (currentPage >= totalPages - 2) {
                          pageNum = totalPages - 4 + i;
                        } else {
                          pageNum = currentPage - 2 + i;
                        }
                        return (
                          <Button
                            key={pageNum}
                            variant={currentPage === pageNum ? "default" : "outline"}
                            size="sm"
                            onClick={() => setCurrentPage(pageNum)}
                            className="h-8 w-8 p-0"
                          >
                            {pageNum}
                          </Button>
                        );
                      })}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                    >
                      Next
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Log Detail Modal */}
      <Dialog open={isDetailModalOpen} onOpenChange={setIsDetailModalOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Email Delivery Details</DialogTitle>
            <DialogDescription>
              Complete information about this email delivery
            </DialogDescription>
          </DialogHeader>
          
          {selectedLog && (
            <div className="space-y-6">
              {/* Status Badge */}
              <div className="flex items-center gap-2">
                <Badge variant={getStatusVariant(selectedLog.delivery_status)} className="gap-1 text-sm">
                  {getStatusIcon(selectedLog.delivery_status)}
                  {selectedLog.delivery_status}
                </Badge>
                {selectedLog.trigger_type && (
                  <Badge variant="outline">{selectedLog.trigger_type}</Badge>
                )}
              </div>

              {/* Basic Info */}
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <Label className="text-muted-foreground">Recipient</Label>
                  <p className="font-medium">{selectedLog.recipient_email}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Sender</Label>
                  <p className="font-medium">{selectedLog.sender_email || '-'}</p>
                </div>
                <div className="sm:col-span-2">
                  <Label className="text-muted-foreground">Subject</Label>
                  <p className="font-medium">{selectedLog.subject}</p>
                </div>
              </div>

              {/* Timeline */}
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-lg border p-3">
                  <div className="text-xs text-muted-foreground">Sent At</div>
                  <div className="text-sm font-medium">{formatDate(selectedLog.sent_at)}</div>
                </div>
                <div className="rounded-lg border p-3">
                  <div className="text-xs text-muted-foreground">Delivered At</div>
                  <div className="text-sm font-medium">{formatDate(selectedLog.delivered_at)}</div>
                </div>
                <div className="rounded-lg border p-3">
                  <div className="text-xs text-muted-foreground">Opened At</div>
                  <div className="text-sm font-medium">{formatDate(selectedLog.opened_at)}</div>
                </div>
                <div className="rounded-lg border p-3">
                  <div className="text-xs text-muted-foreground">Clicked At</div>
                  <div className="text-sm font-medium">{formatDate(selectedLog.clicked_at)}</div>
                </div>
              </div>

              {/* Engagement Stats */}
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="rounded-lg bg-blue-50 dark:bg-blue-950 p-4">
                  <div className="text-2xl font-bold text-blue-600">{selectedLog.open_count}</div>
                  <div className="text-sm text-muted-foreground">Opens</div>
                </div>
                <div className="rounded-lg bg-purple-50 dark:bg-purple-950 p-4">
                  <div className="text-2xl font-bold text-purple-600">{selectedLog.click_count}</div>
                  <div className="text-sm text-muted-foreground">Clicks</div>
                </div>
                <div className="rounded-lg bg-gray-50 dark:bg-gray-900 p-4">
                  <div className="text-sm font-medium">{selectedLog.provider_name || 'Unknown'}</div>
                  <div className="text-sm text-muted-foreground">Provider</div>
                </div>
              </div>

              {/* Error Info */}
              {(selectedLog.error_message || selectedLog.bounce_reason) && (
                <div className="rounded-lg border border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950 p-4">
                  <div className="font-medium text-red-600">Error Information</div>
                  {selectedLog.bounce_type && (
                    <p className="text-sm mt-1"><strong>Bounce Type:</strong> {selectedLog.bounce_type}</p>
                  )}
                  {selectedLog.bounce_reason && (
                    <p className="text-sm mt-1"><strong>Bounce Reason:</strong> {selectedLog.bounce_reason}</p>
                  )}
                  {selectedLog.error_message && (
                    <p className="text-sm mt-1"><strong>Error:</strong> {selectedLog.error_message}</p>
                  )}
                </div>
              )}

              {/* Email Body Preview */}
              {selectedLog.email_template_body && (
                <div>
                  <Label className="text-muted-foreground">Email Preview</Label>
                  <div 
                    className="mt-2 rounded-lg border p-4 max-h-[300px] overflow-auto bg-white dark:bg-gray-950"
                    dangerouslySetInnerHTML={{ __html: selectedLog.email_template_body }}
                  />
                </div>
              )}
            </div>
          )}

          <DialogFooter className="gap-2 sm:gap-0">
            {selectedLog && (selectedLog.delivery_status === 'FAILED' || selectedLog.delivery_status === 'BOUNCED') && (
              <Button 
                variant="outline" 
                onClick={() => handleResend(selectedLog.id)}
                disabled={isSubmitting}
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Resend Email
              </Button>
            )}
            {selectedLog && (
              <Button variant="outline" onClick={() => { setIsDetailModalOpen(false); openForwardModal(selectedLog); }}>
                <Forward className="mr-2 h-4 w-4" />
                Forward Email
              </Button>
            )}
            <Button variant="secondary" onClick={() => setIsDetailModalOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Forward Email Modal */}
      <Dialog open={isForwardModalOpen} onOpenChange={setIsForwardModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Forward Email</DialogTitle>
            <DialogDescription>
              Forward this email to a different recipient
            </DialogDescription>
          </DialogHeader>
          
          {selectedLog && (
            <div className="space-y-4">
              <div className="rounded-lg bg-muted p-3">
                <div className="text-sm">
                  <strong>Original Recipient:</strong> {selectedLog.recipient_email}
                </div>
                <div className="text-sm mt-1">
                  <strong>Subject:</strong> {selectedLog.subject}
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="forward-email">New Recipient Email *</Label>
                <Input
                  id="forward-email"
                  type="email"
                  placeholder="recipient@example.com"
                  value={forwardEmail}
                  onChange={(e) => setForwardEmail(e.target.value)}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="forward-reason">Reason (optional)</Label>
                <Textarea
                  id="forward-reason"
                  placeholder="Reason for forwarding..."
                  value={forwardReason}
                  onChange={(e) => setForwardReason(e.target.value)}
                  rows={3}
                />
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsForwardModalOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleForward} 
              disabled={!forwardEmail || isSubmitting}
            >
              {isSubmitting ? 'Forwarding...' : 'Forward Email'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
