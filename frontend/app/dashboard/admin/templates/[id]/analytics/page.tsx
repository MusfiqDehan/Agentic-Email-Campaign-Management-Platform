'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import api from '@/config/axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  ArrowLeft, BarChart3, TrendingUp, Users, Building2, 
  FileText, Calendar, Clock, GitBranch, Copy
} from 'lucide-react';
import { toast } from 'sonner';
import { getCategoryInfo, getApprovalStatusInfo, formatVersion, formatDate } from '@/config/template-utils';

interface Organization {
  organization__id: string;
  organization__name: string;
  usage_count: number;
}

interface VersionDistribution {
  version: number;
  count: number;
}

interface UsageLog {
  id: string;
  organization_name?: string;
  user_name?: string;
  template_version_at_duplication: number;
  duplicated_at: string;
  duplicated_template_name?: string;
}

interface Template {
  id: string;
  template_name: string;
  email_subject: string;
  category: string;
  is_global: boolean;
  approval_status: string;
  version: number;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

interface Analytics {
  total_usage: number;
  unique_organizations: number;
  organizations: Organization[];
  version_distribution: VersionDistribution[];
  recent_usage: UsageLog[];
  adoption_rate: number;
}

interface AnalyticsData {
  template: Template;
  analytics: Analytics;
}

export default function TemplateAnalyticsPage() {
  const params = useParams();
  const router = useRouter();
  const templateId = params.id as string;
  
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      setIsLoading(true);
      try {
        const response = await api.get(`/campaigns/admin/templates/${templateId}/analytics/`);
        setData(response.data.data);
      } catch (error) {
        console.error(error);
        toast.error('Failed to fetch template analytics');
        router.push('/dashboard/admin/templates');
      } finally {
        setIsLoading(false);
      }
    };

    if (templateId) {
      fetchAnalytics();
    }
  }, [templateId, router]);

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto" />
            <p className="mt-4 text-muted-foreground">Loading analytics...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="p-12 text-center">
            <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No analytics data</h3>
            <p className="text-muted-foreground mb-4">
              Could not load analytics for this template
            </p>
            <Link href="/dashboard/admin/templates">
              <Button variant="outline">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Templates
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { template, analytics } = data;
  const categoryInfo = getCategoryInfo(template.category?.toLowerCase() || 'other');
  const statusInfo = getApprovalStatusInfo(template.approval_status);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/dashboard/admin/templates">
            <Button variant="outline" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold">{template.template_name}</h1>
              <Badge variant={template.is_global ? "default" : "secondary"}>
                {template.is_global ? "Global" : "Organization"}
              </Badge>
            </div>
            <p className="text-muted-foreground">{template.email_subject}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className={categoryInfo.color}>
            <span className="mr-1">{categoryInfo.icon}</span>
            {categoryInfo.label}
          </Badge>
          <Badge className={statusInfo.color}>
            {statusInfo.label}
          </Badge>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Usage</CardTitle>
            <Copy className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.total_usage}</div>
            <p className="text-xs text-muted-foreground">Times duplicated</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Organizations</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.unique_organizations}</div>
            <p className="text-xs text-muted-foreground">Using this template</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Adoption Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.adoption_rate}%</div>
            <p className="text-xs text-muted-foreground">Of all organizations</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Version</CardTitle>
            <GitBranch className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatVersion(template.version)}</div>
            <p className="text-xs text-muted-foreground">Latest version</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Organizations Using Template */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              Organizations Using Template
            </CardTitle>
            <CardDescription>
              Organizations that have duplicated this template
            </CardDescription>
          </CardHeader>
          <CardContent>
            {analytics.organizations.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Users className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No organizations using this template yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {analytics.organizations.map((org, index) => (
                  <div 
                    key={org.organization__id || index}
                    className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                        <Building2 className="h-4 w-4 text-primary" />
                      </div>
                      <span className="font-medium">{org.organization__name}</span>
                    </div>
                    <Badge variant="secondary">
                      {org.usage_count} {org.usage_count === 1 ? 'use' : 'uses'}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Version Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GitBranch className="h-5 w-5" />
              Version Distribution
            </CardTitle>
            <CardDescription>
              Which versions organizations are using
            </CardDescription>
          </CardHeader>
          <CardContent>
            {analytics.version_distribution.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <GitBranch className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No version data available</p>
              </div>
            ) : (
              <div className="space-y-3">
                {analytics.version_distribution.map((item, index) => {
                  const percentage = analytics.total_usage > 0 
                    ? Math.round((item.count / analytics.total_usage) * 100) 
                    : 0;
                  const isLatest = item.version === template.version;
                  
                  return (
                    <div key={index} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{formatVersion(item.version)}</span>
                          {isLatest && (
                            <Badge variant="outline" className="text-xs">Latest</Badge>
                          )}
                        </div>
                        <span className="text-muted-foreground">
                          {item.count} ({percentage}%)
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-muted overflow-hidden">
                        <div 
                          className={`h-full rounded-full transition-all ${
                            isLatest ? 'bg-green-500' : 'bg-amber-500'
                          }`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Usage */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Recent Usage
          </CardTitle>
          <CardDescription>
            Latest template duplications
          </CardDescription>
        </CardHeader>
        <CardContent>
          {analytics.recent_usage.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Calendar className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No recent usage</p>
            </div>
          ) : (
            <div className="space-y-3">
              {analytics.recent_usage.map((usage, index) => (
                <div 
                  key={usage.id || index}
                  className="flex items-center justify-between p-3 rounded-lg border"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-500/10">
                      <FileText className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div>
                      <p className="font-medium">
                        {usage.duplicated_template_name || 'Duplicated Template'}
                      </p>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        {usage.organization_name && (
                          <span>{usage.organization_name}</span>
                        )}
                        {usage.user_name && (
                          <>
                            <span>•</span>
                            <span>{usage.user_name}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge variant="outline">
                      {formatVersion(usage.template_version_at_duplication)}
                    </Badge>
                    <p className="text-xs text-muted-foreground mt-1">
                      {formatDate(usage.duplicated_at)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Template Info */}
      <Card>
        <CardHeader>
          <CardTitle>Template Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <p className="text-sm text-muted-foreground">Created</p>
              <p className="font-medium">{formatDate(template.created_at)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Last Updated</p>
              <p className="font-medium">{formatDate(template.updated_at)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Template ID</p>
              <p className="font-mono text-sm">{template.id}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
