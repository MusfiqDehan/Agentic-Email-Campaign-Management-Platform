'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import api from '@/config/axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Plus, FileText, Trash2, Search, MoreHorizontal, Edit, Copy, Mail, 
  AlertTriangle, Globe, Building2, Eye, Download
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { getCategoryInfo, formatDate } from '@/config/template-utils';

interface Template {
  id: string;
  template_name: string;
  email_subject: string;
  email_body?: string;
  preview_text?: string;
  description?: string;
  category: string;
  is_global: boolean;
  version?: number;
  usage_count?: number;
  created_at: string;
  updated_at?: string;
}

export default function TemplatesPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [templateToDelete, setTemplateToDelete] = useState<Template | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  
  // View dialog state
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  
  // Duplicate dialog state
  const [duplicateDialogOpen, setDuplicateDialogOpen] = useState(false);
  const [templateToDuplicate, setTemplateToDuplicate] = useState<Template | null>(null);
  const [isDuplicating, setIsDuplicating] = useState(false);

  const fetchTemplates = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/campaigns/templates/');
      setTemplates(response.data.data || []);
    } catch (error) {
      console.error(error);
      toast.error('Failed to fetch templates');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  // Filter templates by search query
  const filteredTemplates = templates.filter(template =>
    template.template_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    template.email_subject?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Separate global and organization templates
  const globalTemplates = filteredTemplates.filter(t => t.is_global);
  const orgTemplates = filteredTemplates.filter(t => !t.is_global);

  // View template handler
  const handleViewTemplate = (template: Template) => {
    setSelectedTemplate(template);
    setViewDialogOpen(true);
  };

  // Edit template handler
  const handleEditTemplate = (template: Template) => {
    router.push(`/dashboard/templates/${template.id}/edit`);
  };

  // Delete handlers
  const handleDeleteClick = (template: Template) => {
    setTemplateToDelete(template);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!templateToDelete) return;
    
    setIsDeleting(true);
    try {
      await api.delete(`/campaigns/templates/${templateToDelete.id}/`);
      toast.success('Template deleted');
      fetchTemplates();
    } catch (error: any) {
      console.error(error);
      toast.error(error?.response?.data?.detail || 'Failed to delete template');
    } finally {
      setIsDeleting(false);
      setDeleteDialogOpen(false);
      setTemplateToDelete(null);
    }
  };

  // Duplicate handlers
  const handleDuplicateClick = (template: Template) => {
    setTemplateToDuplicate(template);
    setDuplicateDialogOpen(true);
  };

  const handleDuplicateConfirm = async () => {
    if (!templateToDuplicate) return;
    
    setIsDuplicating(true);
    try {
      // For global templates, use the /use/ endpoint to create an org copy
      // For org templates, use the regular duplicate endpoint
      if (templateToDuplicate.is_global) {
        await api.post(`/campaigns/templates/${templateToDuplicate.id}/use/`);
        toast.success('Template added to your organization');
      } else {
        await api.post(`/campaigns/templates/${templateToDuplicate.id}/duplicate/`);
        toast.success('Template duplicated successfully');
      }
      fetchTemplates();
    } catch (error: any) {
      console.error(error);
      toast.error(error?.response?.data?.detail || 'Failed to duplicate template');
    } finally {
      setIsDuplicating(false);
      setDuplicateDialogOpen(false);
      setTemplateToDuplicate(null);
    }
  };

  // Template Card component for reuse
  const TemplateCard = ({ template, isGlobal = false }: { template: Template; isGlobal?: boolean }) => {
    const categoryInfo = getCategoryInfo(template.category?.toLowerCase() || 'other');
    
    return (
      <Card className="group h-full cursor-pointer overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-transform group-hover:scale-110 ${
                isGlobal ? 'bg-purple-500/10' : 'bg-orange-500/10'
              }`}>
                {isGlobal ? (
                  <Globe className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                ) : (
                  <FileText className="h-5 w-5 text-orange-500" />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <CardTitle className="text-base font-semibold truncate group-hover:text-primary transition-colors">
                    {template.template_name}
                  </CardTitle>
                  {isGlobal && (
                    <Badge variant="secondary" className="bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300 text-xs">
                      Global
                    </Badge>
                  )}
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-lg">{categoryInfo.icon}</span>
                  <Badge variant="outline" className={`${categoryInfo.color} text-xs`}>
                    {categoryInfo.label}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {formatDate(template.created_at)}
                </p>
              </div>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-8 w-8 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={(e) => e.stopPropagation()}
                >
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem 
                  className="gap-2"
                  onClick={() => handleViewTemplate(template)}
                >
                  <Eye className="h-4 w-4" />
                  View
                </DropdownMenuItem>
                {!isGlobal && (
                  <DropdownMenuItem 
                    className="gap-2"
                    onClick={() => handleEditTemplate(template)}
                  >
                    <Edit className="h-4 w-4" />
                    Edit
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem 
                  className="gap-2"
                  onClick={() => handleDuplicateClick(template)}
                >
                  {isGlobal ? (
                    <>
                      <Download className="h-4 w-4" />
                      Use Template
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4" />
                      Duplicate
                    </>
                  )}
                </DropdownMenuItem>
                {!isGlobal && (
                  <>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem 
                      className="gap-2 text-destructive focus:text-destructive"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteClick(template);
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                      Delete
                    </DropdownMenuItem>
                  </>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="flex items-center gap-2 rounded-lg bg-muted/50 px-3 py-2">
            <Mail className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            <p className="text-sm text-muted-foreground truncate">
              {template.email_subject || 'No subject'}
            </p>
          </div>
          {template.version && (
            <div className="flex items-center justify-between mt-2 text-xs text-muted-foreground">
              <span>Version {template.version}</span>
              {template.usage_count !== undefined && (
                <span>{template.usage_count} uses</span>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-6 sm:space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">Email Templates</h2>
          <p className="mt-1 text-muted-foreground">
            Create and manage your email designs
          </p>
        </div>
        <Link href="/dashboard/templates/new">
          <Button className="gradient-bg border-0 text-white shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 w-full sm:w-auto">
            <Plus className="mr-2 h-4 w-4" />
            Create Template
          </Button>
        </Link>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search templates..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Templates Tabs */}
      <Tabs defaultValue="my-templates" className="space-y-6">
        <TabsList>
          <TabsTrigger value="my-templates" className="gap-2">
            <Building2 className="h-4 w-4" />
            My Templates ({orgTemplates.length})
          </TabsTrigger>
          <TabsTrigger value="global-templates" className="gap-2">
            <Globe className="h-4 w-4" />
            Global Templates ({globalTemplates.length})
          </TabsTrigger>
        </TabsList>

        {/* My Organization Templates */}
        <TabsContent value="my-templates" className="space-y-4">
          {isLoading ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3].map((i) => (
                <Card key={i} className="animate-pulse">
                  <CardHeader>
                    <div className="h-4 w-1/2 rounded bg-muted" />
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="h-3 w-full rounded bg-muted" />
                      <div className="h-3 w-2/3 rounded bg-muted" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : orgTemplates.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                  <FileText className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="mt-4 text-lg font-semibold">No organization templates</h3>
                <p className="mt-1 text-center text-sm text-muted-foreground max-w-sm">
                  {searchQuery 
                    ? "No templates match your search. Try a different query."
                    : "Create your first email template or use a global template to get started."
                  }
                </p>
                {!searchQuery && (
                  <Link href="/dashboard/templates/new" className="mt-4">
                    <Button className="gradient-bg border-0 text-white">
                      <Plus className="mr-2 h-4 w-4" />
                      Create Template
                    </Button>
                  </Link>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 stagger-animation">
              {orgTemplates.map((template) => (
                <TemplateCard key={template.id} template={template} isGlobal={false} />
              ))}
            </div>
          )}
        </TabsContent>

        {/* Global Templates */}
        <TabsContent value="global-templates" className="space-y-4">
          <Card className="bg-purple-50/50 dark:bg-purple-950/20 border-purple-200 dark:border-purple-800">
            <CardContent className="py-4">
              <div className="flex items-center gap-3">
                <Globe className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                <div>
                  <p className="text-sm font-medium">Global Templates Library</p>
                  <p className="text-xs text-muted-foreground">
                    These templates are available for all organizations. Click &quot;Use Template&quot; to create your own copy.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {isLoading ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3].map((i) => (
                <Card key={i} className="animate-pulse">
                  <CardHeader>
                    <div className="h-4 w-1/2 rounded bg-muted" />
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="h-3 w-full rounded bg-muted" />
                      <div className="h-3 w-2/3 rounded bg-muted" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : globalTemplates.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                  <Globe className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="mt-4 text-lg font-semibold">No global templates available</h3>
                <p className="mt-1 text-center text-sm text-muted-foreground max-w-sm">
                  {searchQuery 
                    ? "No global templates match your search."
                    : "No global templates have been created by the platform administrators yet."
                  }
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 stagger-animation">
              {globalTemplates.map((template) => (
                <TemplateCard key={template.id} template={template} isGlobal={true} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* View Template Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <div className="flex items-center gap-2">
              <DialogTitle className="text-xl">
                {selectedTemplate?.template_name}
              </DialogTitle>
              {selectedTemplate?.is_global && (
                <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                  Global
                </Badge>
              )}
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
                  <p className="mt-1 flex items-center gap-2">
                    <span>{getCategoryInfo(selectedTemplate.category?.toLowerCase() || 'other').icon}</span>
                    {getCategoryInfo(selectedTemplate.category?.toLowerCase() || 'other').label}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Created</label>
                  <p className="mt-1">{formatDate(selectedTemplate.created_at)}</p>
                </div>
                {selectedTemplate.version && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Version</label>
                    <p className="mt-1">v{selectedTemplate.version}</p>
                  </div>
                )}
                {selectedTemplate.usage_count !== undefined && (
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Usage Count</label>
                    <p className="mt-1">{selectedTemplate.usage_count} times</p>
                  </div>
                )}
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
            {selectedTemplate && !selectedTemplate.is_global && (
              <Button onClick={() => {
                setViewDialogOpen(false);
                handleEditTemplate(selectedTemplate);
              }}>
                <Edit className="h-4 w-4 mr-2" />
                Edit Template
              </Button>
            )}
            {selectedTemplate?.is_global && (
              <Button onClick={() => {
                setViewDialogOpen(false);
                handleDuplicateClick(selectedTemplate);
              }}>
                <Download className="h-4 w-4 mr-2" />
                Use Template
              </Button>
            )}
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

      {/* Duplicate Confirmation Dialog */}
      <AlertDialog open={duplicateDialogOpen} onOpenChange={setDuplicateDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-purple-100 dark:bg-purple-900/40">
                {templateToDuplicate?.is_global ? (
                  <Download className="h-6 w-6 text-purple-600" />
                ) : (
                  <Copy className="h-6 w-6 text-purple-600" />
                )}
              </div>
              <div>
                <AlertDialogTitle>
                  {templateToDuplicate?.is_global ? 'Use Global Template' : 'Duplicate Template'}
                </AlertDialogTitle>
                <AlertDialogDescription>
                  {templateToDuplicate?.is_global 
                    ? `This will create a copy of "${templateToDuplicate?.template_name}" in your organization templates that you can customize.`
                    : `This will create a copy of "${templateToDuplicate?.template_name}" that you can edit independently.`
                  }
                </AlertDialogDescription>
              </div>
            </div>
          </AlertDialogHeader>
          <AlertDialogFooter className="mt-4">
            <AlertDialogCancel disabled={isDuplicating}>Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleDuplicateConfirm}
              disabled={isDuplicating}
            >
              {isDuplicating ? 'Creating...' : templateToDuplicate?.is_global ? 'Use Template' : 'Duplicate'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
