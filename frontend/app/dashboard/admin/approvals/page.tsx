'use client';

import { useEffect, useState } from 'react';
import api from '@/config/axios';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { CheckSquare, Clock, X, Check, Search } from 'lucide-react';
import { toast } from 'sonner';
import { formatRelativeTime } from '@/config/template-utils';

interface ApprovalRequest {
  id: string;
  template: {
    id: string;
    name: string;
    version: number;
  };
  requested_by: {
    id: string;
    name: string;
    email: string;
  };
  status: 'pending' | 'approved' | 'rejected';
  notes?: string;
  created_at: string;
}

export default function PendingApprovalsPage() {
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchApprovals = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/campaigns/admin/approvals/pending/');
      setApprovals(response.data.data || []);
    } catch (error) {
      console.error(error);
      toast.error('Failed to fetch approvals');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
  }, []);

  const handleReview = async (id: string, action: 'approve' | 'reject', notes?: string) => {
    try {
      await api.post(`/campaigns/approvals/${id}/review/`, {
        action,
        notes,
      });
      toast.success(`Template ${action}d successfully`);
      fetchApprovals();
    } catch {
      toast.error(`Failed to ${action} template`);
    }
  };

  const filteredApprovals = approvals.filter(approval =>
    approval.template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    approval.requested_by.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Pending Approvals</h1>
        <p className="text-muted-foreground">
          Review and approve template update requests
        </p>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search approvals..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Badge variant="secondary" className="text-sm">
          {filteredApprovals.length} pending
        </Badge>
      </div>

      <div className="space-y-4">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto" />
            <p className="mt-4 text-muted-foreground">Loading approvals...</p>
          </div>
        ) : filteredApprovals.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <CheckSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No pending approvals</h3>
              <p className="text-muted-foreground">
                All template updates have been reviewed
              </p>
            </CardContent>
          </Card>
        ) : (
          filteredApprovals.map((approval) => (
            <Card key={approval.id}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="font-semibold text-lg">
                        {approval.template.name}
                      </h3>
                      <Badge variant="secondary">
                        v{approval.template.version}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">
                      Requested by {approval.requested_by.name} ({approval.requested_by.email})
                    </p>
                    {approval.notes && (
                      <p className="text-sm bg-muted p-3 rounded-lg mb-2">
                        {approval.notes}
                      </p>
                    )}
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      <span>{formatRelativeTime(approval.created_at)}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleReview(approval.id, 'reject')}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <X className="h-4 w-4 mr-2" />
                      Reject
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => handleReview(approval.id, 'approve')}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <Check className="h-4 w-4 mr-2" />
                      Approve
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
