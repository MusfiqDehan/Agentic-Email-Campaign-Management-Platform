'use client';

import { Campaign } from '@/services/campaigns';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/config/axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Plus, Send, Search, Filter, MoreHorizontal, Eye, Edit, Trash2, Calendar, Users } from 'lucide-react';
import { toast } from 'sonner';
import { Input } from '@/components/ui/input';
import { useTrackCampaignUpdates } from '@/hooks/useTrackCampaignUpdates';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

export default function CampaignsPage() {
  const [initialCampaigns, setInitialCampaigns] = useState<Campaign[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Use real-time campaign tracking
  const { campaigns, setCampaigns } = useTrackCampaignUpdates(initialCampaigns, (campaign) => {
    // Toast on campaign status change
    toast.info(`Campaign "${campaign.name}" status: ${campaign.status}`);
  });

  const fetchCampaigns = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/campaigns/');
      const data = Array.isArray(response.data) ? response.data : (response.data.data || []);
      setInitialCampaigns(data);
    } catch (error) {
      console.error(error);
      toast.error('Failed to fetch campaigns');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const getStatusVariant = (status: string): "default" | "secondary" | "destructive" | "outline" | "success" | "info" | "warning" | "purple" => {
    switch (status) {
      case 'SENT': return 'success';
      case 'SENDING': return 'info';
      case 'DRAFT': return 'secondary';
      case 'SCHEDULED': return 'warning';
      case 'PAUSED': return 'warning';
      case 'CANCELLED': return 'destructive';
      default: return 'secondary';
    }
  };

  const filteredCampaigns = campaigns.filter(campaign =>
    campaign.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    campaign.subject.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 sm:space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">Campaigns</h2>
          <p className="mt-1 text-muted-foreground">
            Manage and track your email campaigns
          </p>
        </div>
        <Link href="/dashboard/campaigns/new">
          <Button className="gradient-bg border-0 text-white shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 w-full sm:w-auto">
            <Plus className="mr-2 h-4 w-4" />
            New Campaign
          </Button>
        </Link>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search campaigns..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button variant="outline" size="icon" className="hidden sm:flex">
          <Filter className="h-4 w-4" />
        </Button>
      </div>

      {/* Campaigns List */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="h-12 w-12 rounded-xl bg-muted" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 w-1/3 rounded bg-muted" />
                    <div className="h-3 w-1/2 rounded bg-muted" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="space-y-3 stagger-animation">
          {filteredCampaigns.map((campaign) => (
            <Card 
              key={campaign.id} 
              className="group overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5"
            >
              <CardContent className="p-4 sm:p-6">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-start gap-4">
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-primary/10 transition-transform group-hover:scale-110">
                      <Send className="h-5 w-5 text-primary" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <Link 
                          href={`/dashboard/campaigns/${campaign.id}`} 
                          className="font-semibold text-lg hover:text-primary transition-colors truncate"
                        >
                          {campaign.name}
                        </Link>
                        <Badge variant={getStatusVariant(campaign.status)}>
                          {campaign.status}
                        </Badge>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground truncate">
                        {campaign.subject}
                      </p>
                      <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {new Date(campaign.created_at).toLocaleDateString()}
                        </span>
                        <span className="flex items-center gap-1">
                          <Users className="h-3 w-3" />
                          {campaign.total_recipients} recipients
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 sm:shrink-0">
                    <Link href={`/dashboard/campaigns/${campaign.id}`}>
                      <Button variant="outline" size="sm" className="gap-1.5">
                        <Eye className="h-3.5 w-3.5" />
                        <span className="hidden sm:inline">View</span>
                      </Button>
                    </Link>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem className="gap-2">
                          <Edit className="h-4 w-4" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem className="gap-2 text-destructive focus:text-destructive">
                          <Trash2 className="h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          
          {filteredCampaigns.length === 0 && (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                  <Send className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="mt-4 text-lg font-semibold">No campaigns found</h3>
                <p className="mt-1 text-center text-sm text-muted-foreground max-w-sm">
                  {searchQuery 
                    ? "No campaigns match your search. Try a different query."
                    : "Get started by creating your first email campaign."
                  }
                </p>
                {!searchQuery && (
                  <Link href="/dashboard/campaigns/new" className="mt-4">
                    <Button className="gradient-bg border-0 text-white">
                      <Plus className="mr-2 h-4 w-4" />
                      Create Campaign
                    </Button>
                  </Link>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
