"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';
import { BarChart3, Users, Send, Mail, Loader2, CheckCircle2, Clock, MailWarning, TrendingUp, ArrowUpRight, Plus } from 'lucide-react';
import api from '@/lib/axios';
import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatDistanceToNow } from 'date-fns';

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchStats = async () => {
    try {
      const response = await api.get('/campaigns/org/stats/');
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch dashboard stats', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();

    const handleRefresh = () => fetchStats();
    window.addEventListener('agent-action-completed', handleRefresh);
    return () => window.removeEventListener('agent-action-completed', handleRefresh);
  }, []);

  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="h-16 w-16 rounded-full border-4 border-primary/20" />
            <div className="absolute inset-0 h-16 w-16 animate-spin rounded-full border-4 border-transparent border-t-primary" />
          </div>
          <p className="text-sm text-muted-foreground animate-pulse">Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  const statsCards = [
    {
      title: "Total Campaigns",
      value: stats?.total_campaigns || 0,
      icon: Send,
      color: "text-primary",
      bgColor: "bg-primary/10",
      change: "+12%",
      changeType: "positive"
    },
    {
      title: "Total Contacts",
      value: stats?.total_contacts?.toLocaleString() || 0,
      icon: Users,
      color: "text-blue-500",
      bgColor: "bg-blue-500/10",
      change: "+8%",
      changeType: "positive"
    },
    {
      title: "Emails Sent",
      value: stats?.emails_sent?.toLocaleString() || 0,
      icon: Mail,
      color: "text-green-500",
      bgColor: "bg-green-500/10",
      change: "+23%",
      changeType: "positive"
    },
    {
      title: "Open Rate",
      value: `${stats?.open_rate || 0}%`,
      icon: BarChart3,
      color: "text-orange-500",
      bgColor: "bg-orange-500/10",
      change: "+5%",
      changeType: "positive"
    },
  ];

  return (
    <div className="space-y-6 sm:space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Welcome back, <span className="gradient-text">{user?.first_name || 'there'}</span> 👋
          </h2>
          <p className="mt-1 text-muted-foreground">
            Here's what's happening with your campaigns today.
          </p>
        </div>
        <Link href="/dashboard/campaigns/new">
          <Button className="gradient-bg border-0 text-white shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30">
            <Plus className="mr-2 h-4 w-4" />
            New Campaign
          </Button>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 stagger-animation">
        {statsCards.map((stat, index) => (
          <Card key={index} className="group overflow-hidden hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
              <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${stat.bgColor} transition-transform group-hover:scale-110`}>
                <stat.icon className={`h-5 w-5 ${stat.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-end justify-between">
                <div>
                  <div className="text-2xl font-bold sm:text-3xl">{stat.value}</div>
                  <div className="flex items-center gap-1 mt-1">
                    <TrendingUp className="h-3 w-3 text-green-500" />
                    <span className="text-xs text-green-500 font-medium">{stat.change}</span>
                    <span className="text-xs text-muted-foreground">vs last month</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Campaigns & Activity */}
      <div className="grid gap-4 lg:gap-6 lg:grid-cols-7">
        <Card className="lg:col-span-4">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Send className="h-5 w-5 text-primary" />
              Recent Campaigns
            </CardTitle>
            <Link href="/dashboard/campaigns">
              <Button variant="ghost" size="sm" className="gap-1">
                View all
                <ArrowUpRight className="h-3 w-3" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {stats?.recent_campaigns?.length > 0 ? (
              <div className="space-y-3">
                {stats.recent_campaigns.map((campaign: any) => (
                  <Link 
                    key={campaign.id} 
                    href={`/dashboard/campaigns/${campaign.id}`}
                    className="flex items-center justify-between rounded-xl border border-border bg-card p-4 transition-all hover:bg-accent hover:shadow-md hover:-translate-y-0.5"
                  >
                    <div className="flex flex-col gap-1 min-w-0 flex-1 mr-4">
                      <span className="font-medium truncate">
                        {campaign.name}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatDistanceToNow(new Date(campaign.created_at), { addSuffix: true })}
                      </span>
                    </div>
                    <Badge 
                      variant={
                        campaign.status === 'SENT' ? 'success' :
                        campaign.status === 'SENDING' ? 'info' :
                        campaign.status === 'DRAFT' ? 'secondary' : 
                        campaign.status === 'SCHEDULED' ? 'warning' : 'default'
                      }
                    >
                      {campaign.status}
                    </Badge>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                  <Send className="h-6 w-6 text-muted-foreground" />
                </div>
                <p className="mt-3 text-sm font-medium">No campaigns yet</p>
                <p className="text-xs text-muted-foreground">Create your first campaign to get started</p>
                <Link href="/dashboard/campaigns/new" className="mt-4">
                  <Button size="sm">Create Campaign</Button>
                </Link>
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card className="lg:col-span-3">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-primary" />
              Recent Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            {stats?.recent_activity?.length > 0 ? (
              <div className="space-y-4">
                {stats.recent_activity.map((log: any) => (
                  <div key={log.id} className="flex items-start gap-3">
                    <div className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                      log.status === 'DELIVERED' || log.status === 'SENT' 
                        ? 'bg-green-500/10' 
                        : log.status === 'BOUNCED' || log.status === 'FAILED'
                        ? 'bg-red-500/10'
                        : 'bg-muted'
                    }`}>
                      {log.status === 'DELIVERED' || log.status === 'SENT' ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : log.status === 'BOUNCED' || log.status === 'FAILED' ? (
                        <MailWarning className="h-4 w-4 text-red-500" />
                      ) : (
                        <Clock className="h-4 w-4 text-muted-foreground" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{log.recipient}</p>
                      <p className="text-xs text-muted-foreground truncate">{log.campaign_name}</p>
                    </div>
                    <div className="text-[10px] text-muted-foreground shrink-0 whitespace-nowrap">
                      {formatDistanceToNow(new Date(log.sent_at), { addSuffix: true })}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                  <Clock className="h-6 w-6 text-muted-foreground" />
                </div>
                <p className="mt-3 text-sm font-medium">No activity yet</p>
                <p className="text-xs text-muted-foreground">Activity will appear here once you start sending</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
