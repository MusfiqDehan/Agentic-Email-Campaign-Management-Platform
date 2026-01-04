'use client';

import { useCallback, useEffect, useState } from 'react';
import api from '@/config/axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  FileText, Plus, Search, Edit, BarChart3, 
  TrendingUp, Users, Eye 
} from 'lucide-react';
import { toast } from 'sonner';
import Link from 'next/link';
import {
  getCategoryInfo,
  getApprovalStatusInfo,
  formatVersion,
  formatDate
} from '@/lib/template-utils';
import { TEMPLATE_CATEGORIES } from '@/config/constants';

interface Template {
  id: string;
  name: string;
  subject: string;
  category: string;
  is_global: boolean;
  is_published: boolean;
  approval_status: string;
  version: number;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export default function AdminTemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const fetchTemplates = useCallback(async () => {
    setIsLoading(true);
    try {
      const params: Record<string, string> = {};
      if (selectedCategory !== 'all') {
        params.category = selectedCategory;
      }
      const response = await api.get('/campaigns/admin/templates/', { params });
      setTemplates(response.data.data || []);
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

  const filteredTemplates = templates.filter(template =>
    template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    template.subject.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const globalTemplates = filteredTemplates.filter(t => t.is_global);
  const orgTemplates = filteredTemplates.filter(t => !t.is_global);

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
            <FileText className="h-4 w-4 text-blue-600" />
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
                const categoryInfo = getCategoryInfo(template.category);
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
                          <CardTitle className="text-lg">{template.name}</CardTitle>
                          <p className="text-sm text-muted-foreground mt-1">
                            {template.subject}
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
                        <Badge className={statusInfo.color}>
                          {statusInfo.label}
                        </Badge>
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
                        <Button variant="outline" size="sm" className="flex-1">
                          <Eye className="h-3 w-3 mr-1" />
                          View
                        </Button>
                        <Button variant="outline" size="sm" className="flex-1">
                          <Edit className="h-3 w-3 mr-1" />
                          Edit
                        </Button>
                        <Button variant="outline" size="sm">
                          <BarChart3 className="h-3 w-3" />
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
                const categoryInfo = getCategoryInfo(template.category);
                return (
                  <Card key={template.id}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <span className="text-2xl">{categoryInfo.icon}</span>
                          <div>
                            <h3 className="font-semibold">{template.name}</h3>
                            <p className="text-sm text-muted-foreground">
                              {template.subject}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <Badge variant="secondary" className={categoryInfo.color}>
                            {categoryInfo.label}
                          </Badge>
                          <Badge variant="outline">
                            {template.usage_count} uses
                          </Badge>
                          <Button variant="outline" size="sm">
                            <Eye className="h-4 w-4" />
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
    </div>
  );
}
