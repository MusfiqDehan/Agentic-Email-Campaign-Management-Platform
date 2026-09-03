'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/config/axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  FileText, Plus, Search, Edit, BarChart3, 
  TrendingUp, Users, Eye, Trash2, AlertTriangle, X,
  CheckCircle2, XCircle, Clock, MoreVertical, FileEdit
} from 'lucide-react';
import { toast } from 'sonner';
import Link from 'next/link';
import {
  getCategoryInfo,
  getApprovalStatusInfo,
  formatVersion,
  formatDate
} from '@/config/template-utils';
import { TEMPLATE_CATEGORIES } from '@/config/constants';

interface Template {
  id: string;
  template_name: string;
  email_subject: string;
  category: string;
  is_global: boolean;
  is_published: boolean;
  approval_status: string;
  version: number;
  usage_count: number;
  created_at: string;
  updated_at: string;
  email_body?: string;
  text_body?: string;
  preview_text?: string;
  description?: string;
  organization?: {
    id: string;
    name: string;
  };
}

const normalizeToLower = (value?: string | null) =>
  typeof value === 'string' ? value.toLowerCase() : '';

export default function AdminTemplatesPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  
  // View dialog state
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  
  // Delete dialog state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [templateToDelete, setTemplateToDelete] = useState<Template | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  
  // Approval status update state
  const [isUpdatingStatus, setIsUpdatingStatus] = useState<string | null>(null);

  const fetchTemplates = useCallback(async () => {
    setIsLoading(true);
    try {
      const params: Record<string, string> = {};
      if (selectedCategory !== 'all') {
        params.category = selectedCategory;
      }
      const response = await api.get('/campaigns/admin/templates/', { params });
      const rawTemplates = Array.isArray(response?.data?.data)
        ? response.data.data
        : [];

      const sanitizedTemplates: Template[] = rawTemplates
        .filter(
          (template: any) =>
            typeof template === 'object' &&
            template !== null &&
            typeof template.id === 'string'
        )
        .map((template: any) => ({
          ...template,
          template_name: template?.template_name ?? 'Untitled template',
          email_subject: template?.email_subject ?? 'No subject provided',
          category: template?.category ?? 'OTHER',
          approval_status: template?.approval_status ?? 'PENDING_APPROVAL',
          version: template?.version ?? 1,
          usage_count: template?.usage_count ?? 0,
          created_at: template?.created_at ?? template?.updated_at ?? '',
          updated_at: template?.updated_at ?? template?.created_at ?? '',
          is_global: Boolean(template?.is_global),
          is_published: Boolean(template?.is_published),
        }));

      setTemplates(sanitizedTemplates);
    } catch (error) {
      console.error(error);
      toast.error('Failed to fetch templates');
    } finally {
      setIsLoading(false);
    }
  }, [selectedCategory]);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const normalizedQuery = searchQuery.trim().toLowerCase();

  const filteredTemplates = templates.filter((template) => {
    if (!normalizedQuery) {
      return true;
    }

    return (
      normalizeToLower(template?.template_name).includes(normalizedQuery) ||
      normalizeToLower(template?.email_subject).includes(normalizedQuery)
    );
  });

  // Global templates page only shows APPROVED templates
  // Draft/Pending/Rejected are shown in the Approvals page
  const globalTemplates = filteredTemplates.filter(t => t.is_global && t.approval_status === 'APPROVED');
  const orgTemplates = filteredTemplates.filter(t => !t.is_global);

  // View template handler
  const handleViewTemplate = (template: Template) => {
    setSelectedTemplate(template);
    setViewDialogOpen(true);
  };

  // Edit template handler  
  const handleEditTemplate = (template: Template) => {
    router.push(`/dashboard/admin/templates/${template.id}/edit`);
  };

  // Delete template handlers
  const handleDeleteClick = (template: Template) => {
    setTemplateToDelete(template);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!templateToDelete) return;
    
    setIsDeleting(true);
    try {
      await api.delete(`/campaigns/admin/templates/${templateToDelete.id}/`);
      toast.success('Template deleted successfully');
      fetchTemplates();
    } catch (error: any) {
      console.error(error);
      const message = error?.response?.data?.detail || 'Failed to delete template';
      toast.error(message);
    } finally {
      setIsDeleting(false);
      setDeleteDialogOpen(false);
      setTemplateToDelete(null);
    }
  };

  // View analytics handler
  const handleViewAnalytics = (template: Template) => {
    router.push(`/dashboard/admin/templates/${template.id}/analytics`);
  };

  // Update approval status handler
  const handleUpdateApprovalStatus = async (template: Template, newStatus: string) => {
    setIsUpdatingStatus(template.id);
    try {
      await api.patch(`/campaigns/admin/templates/${template.id}/`, {
        approval_status: newStatus
      });
      toast.success(`Template status updated to ${newStatus.replace('_', ' ').toLowerCase()}`);
      fetchTemplates();
    } catch (error: any) {
      console.error(error);
      const message = error?.response?.data?.detail || 'Failed to update approval status';
      toast.error(message);
    } finally {
      setIsUpdatingStatus(null);
    }
  };

  // Approval status options
  const approvalStatusOptions = [
    { value: 'DRAFT', label: 'Draft', icon: FileEdit, color: 'text-gray-500' },
    { value: 'PENDING_APPROVAL', label: 'Pending Approval', icon: Clock, color: 'text-yellow-500' },
    { value: 'APPROVED', label: 'Approved', icon: CheckCircle2, color: 'text-green-500' },
    { value: 'REJECTED', label: 'Rejected', icon: XCircle, color: 'text-red-500' },
  ];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Template Management</h1>
          <p className="text-muted-foreground">
            Manage global and organization templates
          </p>
        </div>
        <Link href="/dashboard/admin/templates/create">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Create Global Template
          </Button>
        </Link>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Templates</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{templates.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Global Templates</CardTitle>
            <FileText className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{globalTemplates.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Org Templates</CardTitle>
            <Users className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{orgTemplates.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Usage</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {templates.reduce((sum, t) => sum + t.usage_count, 0)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
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
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="px-4 py-2 border rounded-lg"
        >
          <option value="all">All Categories</option>
          {TEMPLATE_CATEGORIES.map((cat) => (
            <option key={cat.value} value={cat.value}>
              {cat.icon} {cat.label}
            </option>
          ))}
        </select>
      </div>

      {/* Templates Tabs */}
      <Tabs defaultValue="global" className="space-y-4">
        <TabsList>
          <TabsTrigger value="global">
            Global Templates ({globalTemplates.length})
          </TabsTrigger>
          <TabsTrigger value="organizations">
            Organization Templates ({orgTemplates.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="global" className="space-y-4">
          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto" />
              <p className="mt-4 text-muted-foreground">Loading templates...</p>
            </div>
          ) : globalTemplates.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No global templates</h3>
                <p className="text-muted-foreground mb-4">
                  Create your first global template to get started
                </p>
                <Link href="/dashboard/admin/templates/create">
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Create Template
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {globalTemplates.map((template) => {
                const categoryInfo = getCategoryInfo(template.category.toLowerCase());
                const statusInfo = getApprovalStatusInfo(template.approval_status);
                return (
                  <Card key={template.id} className="hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-2xl">{categoryInfo.icon}</span>
                            <Badge variant="secondary" className={categoryInfo.color}>
                              {categoryInfo.label}
                            </Badge>
                          </div>
                          <CardTitle className="text-lg">{template.template_name}</CardTitle>
                          <p className="text-sm text-muted-foreground mt-1">
                            {template.email_subject}
                          </p>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Version</span>
                        <Badge variant="outline">{formatVersion(template.version)}</Badge>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Status</span>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              className="h-auto p-0 hover:bg-transparent"
                              disabled={isUpdatingStatus === template.id}
                            >
                              <Badge className={`${statusInfo.color} cursor-pointer hover:opacity-80`}>
                                {isUpdatingStatus === template.id ? 'Updating...' : statusInfo.label}
                              </Badge>
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Change Status</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            {approvalStatusOptions.map((option) => {
                              const Icon = option.icon;
                              const isActive = template.approval_status === option.value;
                              return (
                                <DropdownMenuItem
                                  key={option.value}
                                  onClick={() => handleUpdateApprovalStatus(template, option.value)}
                                  disabled={isActive}
                                  className={isActive ? 'bg-muted' : ''}
                                >
                                  <Icon className={`h-4 w-4 mr-2 ${option.color}`} />
                                  {option.label}
                                  {isActive && <span className="ml-auto text-xs text-muted-foreground">(current)</span>}
                                </DropdownMenuItem>
                              );
                            })}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Usage</span>
                        <span className="font-medium">{template.usage_count} times</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Updated</span>
                        <span className="text-xs">{formatDate(template.updated_at)}</span>
                      </div>
                      <div className="flex items-center gap-2 pt-2">
                        <Button 
                          variant="outline" 
                          size="sm" 
                          className="flex-1"
                          onClick={() => handleViewTemplate(template)}
                        >
                          <Eye className="h-3 w-3 mr-1" />
                          View
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          className="flex-1"
                          onClick={() => handleEditTemplate(template)}
                        >
                          <Edit className="h-3 w-3 mr-1" />
                          Edit
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleViewAnalytics(template)}
                        >
                          <BarChart3 className="h-3 w-3" />
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm"
                          className="text-destructive hover:text-destructive"
                          onClick={() => handleDeleteClick(template)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="organizations" className="space-y-4">
          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto" />
              <p className="mt-4 text-muted-foreground">Loading templates...</p>
            </div>
          ) : orgTemplates.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No organization templates</h3>
                <p className="text-muted-foreground">
                  Organization-specific templates will appear here
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {orgTemplates.map((template) => {
                const categoryInfo = getCategoryInfo(template.category.toLowerCase());
                return (
                  <Card key={template.id}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <span className="text-2xl">{categoryInfo.icon}</span>
                          <div>
                            <h3 className="font-semibold">{template.template_name}</h3>
                            <p className="text-sm text-muted-foreground">
                              {template.email_subject}
                            </p>
                            {template.organization && (
                              <p className="text-xs text-purple-600 mt-1">
                                {template.organization.name}
                              </p>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <Badge variant="secondary" className={categoryInfo.color}>
                            {categoryInfo.label}
                          </Badge>
                          <Badge variant="outline">
                            {template.usage_count} uses
                          </Badge>
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
                          <Button 
                            variant="outline" 
                            size="sm"
                            className="text-destructive hover:text-destructive"
                            onClick={() => handleDeleteClick(template)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* View Template Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <div className="flex items-center justify-between">
              <DialogTitle className="text-xl">
                {selectedTemplate?.template_name}
              </DialogTitle>
            </div>
            <DialogDescription>
              {selectedTemplate?.email_subject}
            </DialogDescription>
          </DialogHeader>
          
          {selectedTemplate && (
            <div className="space-y-6">
              {/* Template Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Category</label>
                  <p className="mt-1">{getCategoryInfo(selectedTemplate.category.toLowerCase()).label}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Status</label>
                  <div className="mt-1">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="h-auto p-0 hover:bg-transparent"
                          disabled={isUpdatingStatus === selectedTemplate.id}
                        >
                          <Badge className={`${getApprovalStatusInfo(selectedTemplate.approval_status).color} cursor-pointer hover:opacity-80`}>
                            {isUpdatingStatus === selectedTemplate.id ? 'Updating...' : getApprovalStatusInfo(selectedTemplate.approval_status).label}
                          </Badge>
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="start">
                        <DropdownMenuLabel>Change Status</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        {approvalStatusOptions.map((option) => {
                          const Icon = option.icon;
                          const isActive = selectedTemplate.approval_status === option.value;
                          return (
                            <DropdownMenuItem
                              key={option.value}
                              onClick={() => {
                                handleUpdateApprovalStatus(selectedTemplate, option.value);
                                // Update local state for immediate UI feedback
                                setSelectedTemplate({ ...selectedTemplate, approval_status: option.value });
                              }}
                              disabled={isActive}
                              className={isActive ? 'bg-muted' : ''}
                            >
                              <Icon className={`h-4 w-4 mr-2 ${option.color}`} />
                              {option.label}
                              {isActive && <span className="ml-auto text-xs text-muted-foreground">(current)</span>}
                            </DropdownMenuItem>
                          );
                        })}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Version</label>
                  <p className="mt-1">{formatVersion(selectedTemplate.version)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Usage Count</label>
                  <p className="mt-1">{selectedTemplate.usage_count} times</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Type</label>
                  <p className="mt-1">
                    <Badge variant={selectedTemplate.is_global ? "default" : "secondary"}>
                      {selectedTemplate.is_global ? "Global" : "Organization"}
                    </Badge>
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Last Updated</label>
                  <p className="mt-1">{formatDate(selectedTemplate.updated_at)}</p>
                </div>
              </div>

              {/* Preview Text */}
              {selectedTemplate.preview_text && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Preview Text</label>
                  <p className="mt-1 text-sm">{selectedTemplate.preview_text}</p>
                </div>
              )}

              {/* Description */}
              {selectedTemplate.description && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Description</label>
                  <p className="mt-1 text-sm">{selectedTemplate.description}</p>
                </div>
              )}

              {/* Email Body Preview */}
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
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setViewDialogOpen(false)}>
              Close
            </Button>
            <Button onClick={() => {
              setViewDialogOpen(false);
              if (selectedTemplate) handleEditTemplate(selectedTemplate);
            }}>
              <Edit className="h-4 w-4 mr-2" />
              Edit Template
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
                <AlertTriangle className="h-6 w-6 text-destructive" />
              </div>
              <div>
                <AlertDialogTitle>Delete Template</AlertDialogTitle>
                <AlertDialogDescription>
                  Are you sure you want to delete &quot;{templateToDelete?.template_name}&quot;? 
                  {templateToDelete?.usage_count && templateToDelete.usage_count > 0 && (
                    <span className="block mt-1 text-amber-600">
                      Warning: This template has been used {templateToDelete.usage_count} times.
                    </span>
                  )}
                  This action cannot be undone.
                </AlertDialogDescription>
              </div>
            </div>
          </AlertDialogHeader>
          <AlertDialogFooter className="mt-4">
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleDeleteConfirm}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
