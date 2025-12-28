'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus, Send, Pause, Play, XCircle } from 'lucide-react';
import { toast } from 'sonner';

interface Campaign {
  id: string;
  name: string;
  subject: string;
  status: string;
  total_recipients: number;
  created_at: string;
}

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchCampaigns = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/campaigns/');
      const data = Array.isArray(response.data) ? response.data : (response.data.data || []);
      setCampaigns(data);
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SENT': return 'text-green-500 bg-green-50';
      case 'SENDING': return 'text-blue-500 bg-blue-50';
      case 'DRAFT': return 'text-gray-500 bg-gray-50';
      case 'SCHEDULED': return 'text-orange-500 bg-orange-50';
      case 'PAUSED': return 'text-yellow-500 bg-yellow-50';
      case 'CANCELLED': return 'text-red-500 bg-red-50';
      default: return 'text-gray-500 bg-gray-50';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Campaigns</h2>
          <p className="text-muted-foreground">Manage and track your email campaigns.</p>
        </div>
        <Link href="/dashboard/campaigns/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" /> New Campaign
          </Button>
        </Link>
      </div>

      {isLoading ? (
        <div>Loading...</div>
      ) : (
        <div className="grid gap-4">
          {campaigns.map((campaign) => (
            <Card key={campaign.id} className="hover:bg-gray-50 transition-colors">
              <CardContent className="p-6 flex items-center justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-3">
                    <Link href={`/dashboard/campaigns/${campaign.id}`} className="hover:underline">
                      <h3 className="font-semibold text-lg">{campaign.name}</h3>
                    </Link>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(campaign.status)}`}>
                      {campaign.status}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">Subject: {campaign.subject}</p>
                  <p className="text-xs text-muted-foreground">
                    Created: {new Date(campaign.created_at).toLocaleDateString()} • Recipients: {campaign.total_recipients}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Link href={`/dashboard/campaigns/${campaign.id}`}>
                    <Button variant="outline" size="sm">View Details</Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
          {campaigns.length === 0 && (
            <div className="flex h-32 items-center justify-center rounded-lg border border-dashed">
              <p className="text-muted-foreground">No campaigns found.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
