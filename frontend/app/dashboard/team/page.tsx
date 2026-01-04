'use client';

import { useEffect, useState } from 'react';
import api from '@/config/axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { UsersRound, FileText, Bell, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';
import { formatRelativeTime, getCategoryInfo } from '@/lib/template-utils';

interface TemplateUsage {
  id: string;
  user: {
    id: string;
    name: string;
    email: string;
  };
  template: {
    id: string;
    name: string;
    category: string;
  };
  action: string;
  created_at: string;
}

interface TeamStats {
  total_members: number;
  total_templates_used: number;
  most_used_template: {
    name: string;
    usage_count: number;
  };
  active_members_count: number;
}

export default function TeamInsightsPage() {
  const [usageLogs, setUsageLogs] = useState<TemplateUsage[]>([]);
  const [stats, setStats] = useState<TeamStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const [usageResponse, statsResponse] = await Promise.all([
          api.get('/campaigns/organization/template-usage/'),
          api.get('/campaigns/organization/team-template-stats/'),
        ]);
        setUsageLogs(usageResponse.data.data || []);
        setStats(statsResponse.data.data || null);
      } catch (error) {
        console.error(error);
        toast.error('Failed to fetch team insights');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Team Insights</h1>
        <p className="text-muted-foreground">
          Monitor your team&apos;s template usage and activity
        </p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Team Members</CardTitle>
              <UsersRound className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_members}</div>
              <p className="text-xs text-muted-foreground">
                {stats.active_members_count} active
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Templates Used</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_templates_used}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Most Used</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-lg font-bold truncate">
                {stats.most_used_template?.name || 'N/A'}
              </div>
              <p className="text-xs text-muted-foreground">
                {stats.most_used_template?.usage_count || 0} times
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Notifications</CardTitle>
              <Bell className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{usageLogs.length}</div>
              <p className="text-xs text-muted-foreground">Recent activities</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Usage Logs */}
      <Card>
        <CardHeader>
          <CardTitle>Template Usage Activity</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto" />
              <p className="mt-4 text-muted-foreground">Loading activity...</p>
            </div>
          ) : usageLogs.length === 0 ? (
            <div className="text-center py-12">
              <UsersRound className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No activity yet</h3>
              <p className="text-muted-foreground">
                Template usage by your team will appear here
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {usageLogs.map((log) => {
                const categoryInfo = getCategoryInfo(log.template.category);
                return (
                  <div
                    key={log.id}
                    className="flex items-center justify-between p-3 rounded-lg border"
                  >
                    <div className="flex items-center gap-3">
                      <div className="text-2xl">{categoryInfo.icon}</div>
                      <div>
                        <p className="font-medium">
                          {log.user.name} {log.action === 'duplicated' ? 'used' : log.action}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {log.template.name}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge variant="secondary" className={categoryInfo.color}>
                        {categoryInfo.label}
                      </Badge>
                      <p className="text-xs text-muted-foreground mt-1">
                        {formatRelativeTime(log.created_at)}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
