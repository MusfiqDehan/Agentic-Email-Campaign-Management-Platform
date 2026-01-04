'use client';

import { useEffect, useState } from 'react';
import { useRealtimeUpdates } from '@/hooks/useRealtimeUpdates';
import { fetchCampaignById, Campaign } from '@/services/campaigns';
import { toast } from 'sonner';

/**
 * Example: Campaign Detail Page with Real-Time Updates
 * 
 * This shows how to integrate real-time campaign status updates
 * into a campaign detail/view page.
 */

interface CampaignDetailExampleProps {
  campaignId: string;
}

export default function CampaignDetailExample({ campaignId }: CampaignDetailExampleProps) {
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { onCampaignStatusUpdate, isConnected } = useRealtimeUpdates();

  // Load campaign on mount
  useEffect(() => {
    const loadCampaign = async () => {
      try {
        setIsLoading(true);
        const data = await fetchCampaignById(campaignId);
        setCampaign(data);
      } catch (error) {
        console.error('Failed to load campaign:', error);
        toast.error('Failed to load campaign');
      } finally {
        setIsLoading(false);
      }
    };

    loadCampaign();
  }, [campaignId]);

  // Subscribe to real-time updates for this campaign
  useEffect(() => {
    if (!campaign) return;

    const unsubscribe = onCampaignStatusUpdate(
      campaign.id,
      (update) => {
        // Update campaign data when status changes
        setCampaign(prev => {
          if (!prev) return null;
          
          const hasStatusChange = prev.status !== update.status;
          
          if (hasStatusChange) {
            // Show toast notification on status change
            toast.info(
              `Campaign status changed: ${prev.status} → ${update.status}`,
              { duration: 3000 }
            );
          }

          // Update all campaign fields from the update
          return {
            ...prev,
            status: update.status,
            stats_sent: update.stats_sent,
            stats_delivered: update.stats_delivered,
            stats_opened: update.stats_opened,
            stats_clicked: update.stats_clicked,
            stats_total_recipients: update.stats_total_recipients,
            updated_at: update.updated_at
          };
        });
      }
    );

    // Cleanup subscription on unmount
    return unsubscribe;
  }, [campaign?.id, onCampaignStatusUpdate]);

  if (isLoading) {
    return <div>Loading campaign...</div>;
  }

  if (!campaign) {
    return <div>Campaign not found</div>;
  }

  const openRate = campaign.stats_total_recipients > 0 
    ? ((campaign.stats_opened / campaign.stats_total_recipients) * 100).toFixed(2)
    : 0;

  const clickRate = campaign.stats_total_recipients > 0
    ? ((campaign.stats_clicked / campaign.stats_total_recipients) * 100).toFixed(2)
    : 0;

  return (
    <div className="space-y-6">
      {/* Connection Status Indicator */}
      <div className="flex items-center gap-2 text-sm">
        <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
        <span>{isConnected ? 'Live updates enabled' : 'Offline - updates unavailable'}</span>
      </div>

      {/* Campaign Header */}
      <div className="border-b pb-4">
        <h1 className="text-3xl font-bold">{campaign.name}</h1>
        <div className="mt-2 flex items-center gap-2">
          <span className="text-sm text-gray-600">Status:</span>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(campaign.status)}`}>
            {campaign.status}
          </span>
        </div>
      </div>

      {/* Campaign Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard 
          label="Sent"
          value={campaign.stats_sent}
          total={campaign.stats_total_recipients}
        />
        <StatCard 
          label="Delivered"
          value={campaign.stats_delivered}
          total={campaign.stats_total_recipients}
        />
        <StatCard 
          label="Opened"
          value={campaign.stats_opened}
          percentage={openRate}
        />
        <StatCard 
          label="Clicked"
          value={campaign.stats_clicked}
          percentage={clickRate}
        />
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>Sending Progress</span>
          <span className="font-semibold">
            {campaign.stats_sent} / {campaign.stats_total_recipients}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
            style={{
              width: `${(campaign.stats_sent / campaign.stats_total_recipients) * 100}%`
            }}
          />
        </div>
      </div>

      {/* Last Updated */}
      <div className="text-xs text-gray-500">
        Last updated: {campaign.updated_at 
          ? new Date(campaign.updated_at).toLocaleString() 
          : 'Never'}
      </div>
    </div>
  );
}

// Helper Component for Stats
function StatCard({ 
  label, 
  value, 
  total, 
  percentage 
}: { 
  label: string; 
  value: number; 
  total?: number;
  percentage?: string | number;
}) {
  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <p className="text-xs text-gray-600 mb-1">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
      {total && <p className="text-xs text-gray-500">of {total}</p>}
      {percentage !== undefined && <p className="text-xs text-gray-500">{percentage}%</p>}
    </div>
  );
}

// Helper: Get status color
function getStatusColor(status: string): string {
  switch (status) {
    case 'DRAFT':
      return 'bg-gray-100 text-gray-800';
    case 'SCHEDULED':
      return 'bg-yellow-100 text-yellow-800';
    case 'SENDING':
      return 'bg-blue-100 text-blue-800';
    case 'SENT':
      return 'bg-green-100 text-green-800';
    case 'PAUSED':
      return 'bg-orange-100 text-orange-800';
    case 'CANCELLED':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}
