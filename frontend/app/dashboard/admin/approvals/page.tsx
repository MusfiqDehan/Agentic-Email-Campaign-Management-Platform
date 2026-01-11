'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/config/axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
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
  CheckSquare, Clock, Search, FileText, Eye, Edit,
  FileEdit, XCircle, CheckCircle2, MoreVertical
} from 'lucide-react';
import { toast } from 'sonner';
import { getCategoryInfo, getApprovalStatusInfo, formatDate, formatVersion } from '@/config/template-utils';

interface Template {
  id: string;
  template_name: string;
  email_subject: string;
  email_body?: string;
  category: string;
  is_global: boolean;
  approval_status: string;
  version: number;
  created_at: string;
  updated_at: string;
}

export default function PendingApprovalsPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [isUpdatingStatus, setIsUpdatingStatus] = useState<string | null>(null);
  
  // View dialog state
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);

  const fetchTemplates = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/campaigns/admin/approvals/pending/');
      setTemplates(response.data.data || []);
    } catch (error) {
      console.error(error);
      toast.error('Failed to fetch pending templates');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  // Update approval status handler
  const handleUpdateApprovalStatus = async (template: Template, newStatus: string) => {
    setIsUpdatingStatus(template.id);
    try {
      await api.patch(`/campaigns/admin/templates/${template.id}/`, {
        approval_status: newStatus
      });
      
      if (newStatus === 'APPROVED') {
        toast.success(`Template "${template.template_name}" approved successfully`);
      } else if (newStatus === 'REJECTED') {
        toast.success(`Template "${template.template_name}" rejected`);
      } else {
        toast.success(`Template status updated`);
      }
      
      fetchTemplates();
    } catch (error: any) {
      console.error(error);
      const message = error?.response?.data?.detail || 'Failed to update approval status';
      toast.error(message);
    } finally {
      setIsUpdatingStatus(null);
    }
  };

  // View template handler
  const handleViewTemplate = (template: Template) => {
    setSelectedTemplate(template);
    setViewDialogOpen(true);
  };

  // Edit template handler
  const handleEditTemplate = (template: Template) => {
    router.push(`/dashboard/admin/templates/${template.id}/edit`);
  };

  const filteredTemplates = templates.filter(template =>
    template.template_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    template.email_subject?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Separate by status
  const draftTemplates = filteredTemplates.filter(t => t.approval_status === 'DRAFT');
  const pendingTemplates = filteredTemplates.filter(t => t.approval_status === 'PENDING_APPROVAL');
  const rejectedTemplates = filteredTemplates.filter(t => t.approval_status === 'REJECTED');

  const renderTemplateCard = (template: Template) => {
    const categoryInfo = getCategoryInfo(template.category?.toLowerCase() || 'other');
    const statusInfo = getApprovalStatusInfo(template.approval_status);
    
    return (
      <Card key={template.id} className="hover:shadow-md transition-shadow">
        <CardContent className="p-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xl">{categoryInfo.icon}</span>
                <h3 className="font-semibold text-lg truncate">
                  {template.template_name}
                </h3>
                <Badge variant="outline">{formatVersion(template.version)}</Badge>
              </div>
              <p className="text-sm text-muted-foreground mb-2 truncate">
                {template.email_subject}
              </p>
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <Badge variant="secondary" className={categoryInfo.color}>
                  {categoryInfo.label}
                </Badge>
                <Badge className={statusInfo.color}>
                  {statusInfo.label}
                </Badge>
                <span>Created {formatDate(template.created_at)}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleViewTemplate(template)}
              >
                <Eye className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleEditTemplate(template)}
              >
                <Edit className="h-4 w-4" />
              </Button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button 
                    variant="outline" 
                    size="sm"
                    disabled={isUpdatingStatus === template.id}
                  >
                    {isUpdatingStatus === template.id ? (
                      <div className="h-4 w-4 animate-spin border-2 border-primary border-t-transparent rounded-full" />
                    ) : (
                      <MoreVertical className="h-4 w-4" />
                    )}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuLabel>Change Status</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => handleUpdateApprovalStatus(template, 'APPROVED')}
                    className="text-green-600"
                  >
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    Approve
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => handleUpdateApprovalStatus(template, 'REJECTED')}
                    className="text-red-600"
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    Reject
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => handleUpdateApprovalStatus(template, 'DRAFT')}
                    disabled={template.approval_status === 'DRAFT'}
                  >
                    <FileEdit className="h-4 w-4 mr-2" />
                    Move to Draft
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => handleUpdateApprovalStatus(template, 'PENDING_APPROVAL')}
                    disabled={template.approval_status === 'PENDING_APPROVAL'}
                  >
                    <Clock className="h-4 w-4 mr-2" />
                    Mark Pending
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderEmptyState = (status: string) => (
    <Card>
      <CardContent className="p-12 text-center">
        <CheckSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">No {status.toLowerCase()} templates</h3>
        <p className="text-muted-foreground">
          {status === 'draft' && 'New templates will appear here for review'}
          {status === 'pending' && 'Templates awaiting approval will appear here'}
          {status === 'rejected' && 'Rejected templates will appear here'}
        </p>
      </CardContent>
    </Card>
  );

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Template Approvals</h1>
        <p className="text-muted-foreground">
          Review and approve global template submissions
        </p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Draft</CardTitle>
            <FileEdit className="h-4 w-4 text-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{draftTemplates.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Approval</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingTemplates.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Rejected</CardTitle>
            <XCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{rejectedTemplates.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Badge variant="secondary" className="text-sm">
          {filteredTemplates.length} total
        </Badge>
      </div>

      {/* Tabs by Status */}
      <Tabs defaultValue="draft" className="space-y-4">
        <TabsList>
          <TabsTrigger value="draft">
            Draft ({draftTemplates.length})
          </TabsTrigger>
          <TabsTrigger value="pending">
            Pending ({pendingTemplates.length})
          </TabsTrigger>
          <TabsTrigger value="rejected">
            Rejected ({rejectedTemplates.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="draft" className="space-y-4">
          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto" />
              <p className="mt-4 text-muted-foreground">Loading templates...</p>
            </div>
          ) : draftTemplates.length === 0 ? (
            renderEmptyState('draft')
          ) : (
            <div className="space-y-3">
              {draftTemplates.map(renderTemplateCard)}
            </div>
          )}
        </TabsContent>

        <TabsContent value="pending" className="space-y-4">
          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto" />
              <p className="mt-4 text-muted-foreground">Loading templates...</p>
            </div>
          ) : pendingTemplates.length === 0 ? (
            renderEmptyState('pending')
          ) : (
            <div className="space-y-3">
              {pendingTemplates.map(renderTemplateCard)}
            </div>
          )}
        </TabsContent>

        <TabsContent value="rejected" className="space-y-4">
          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto" />
              <p className="mt-4 text-muted-foreground">Loading templates...</p>
            </div>
          ) : rejectedTemplates.length === 0 ? (
            renderEmptyState('rejected')
          ) : (
            <div className="space-y-3">
              {rejectedTemplates.map(renderTemplateCard)}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* View Template Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-xl">
              {selectedTemplate?.template_name}
            </DialogTitle>
            <DialogDescription>
              {selectedTemplate?.email_subject}
            </DialogDescription>
          </DialogHeader>
          
          {selectedTemplate && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Category</label>
                  <p className="mt-1">{getCategoryInfo(selectedTemplate.category?.toLowerCase() || 'other').label}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Status</label>
                  <p className="mt-1">
                    <Badge className={getApprovalStatusInfo(selectedTemplate.approval_status).color}>
                      {getApprovalStatusInfo(selectedTemplate.approval_status).label}
                    </Badge>
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Version</label>
                  <p className="mt-1">{formatVersion(selectedTemplate.version)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Created</label>
                  <p className="mt-1">{formatDate(selectedTemplate.created_at)}</p>
                </div>
              </div>

              {selectedTemplate.email_body && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Email Content Preview</label>
                  <div 
                    className="mt-2 border rounded-lg p-4 bg-muted/30 max-h-[300px] overflow-auto prose prose-sm max-w-none dark:prose-invert"
                    dangerouslySetInnerHTML={{ __html: selectedTemplate.email_body }}
                  />
                </div>
              )}
            </div>
          )}
          
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setViewDialogOpen(false)}>
              Close
            </Button>
            {selectedTemplate && selectedTemplate.approval_status !== 'APPROVED' && (
              <>
                <Button 
                  variant="destructive"
                  onClick={() => {
                    handleUpdateApprovalStatus(selectedTemplate, 'REJECTED');
                    setViewDialogOpen(false);
                  }}
                >
                  <XCircle className="h-4 w-4 mr-2" />
                  Reject
                </Button>
                <Button 
                  className="bg-green-600 hover:bg-green-700"
                  onClick={() => {
                    handleUpdateApprovalStatus(selectedTemplate, 'APPROVED');
                    setViewDialogOpen(false);
                  }}
                >
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  Approve
                </Button>
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}