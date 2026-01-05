'use client';

import { useEffect, useState } from 'react';
import { useTrackCampaignUpdates } from '@/hooks/useTrackCampaignUpdates';
import { fetchCampaigns, Campaign } from '@/services/campaigns';
import { toast } from 'sonner';

/**
 * Example: Campaign List with Real-Time Status Updates
 * 
 * This shows how to integrate real-time updates into a campaign list
 * that displays multiple campaigns with live status updates.
 */

export default function CampaignListExample() {
  const [initialCampaigns, setInitialCampaigns] = useState<Campaign[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [updatedCampaignIds, setUpdatedCampaignIds] = useState<Set<string>>(new Set());

  // Use real-time campaign tracking
  const { campaigns, updateCampaign } = useTrackCampaignUpdates(
    initialCampaigns,
    (campaign) => {
      // Show toast notification when a campaign is updated
      toast.info(
        `${campaign.name} is now ${campaign.status.toLowerCase()}`,
        { duration: 2000 }
      );

      // Highlight the updated campaign briefly
      setUpdatedCampaignIds(prev => new Set(prev).add(campaign.id));
      setTimeout(() => {
        setUpdatedCampaignIds(prev => {
          const next = new Set(prev);
          next.delete(campaign.id);
          return next;
        });
      }, 2000);
    }
  );

  // Load campaigns on mount
  useEffect(() => {
    const loadCampaigns = async () => {
      try {
        setIsLoading(true);
        const response = await fetchCampaigns();
        setInitialCampaigns(response.results);
      } catch (error) {
        console.error('Failed to load campaigns:', error);
        toast.error('Failed to load campaigns');
      } finally {
        setIsLoading(false);
      }
    };

    loadCampaigns();
  }, []);

  if (isLoading) {
    return <div className="text-center py-8">Loading campaigns...</div>;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Live Campaign Status</h2>
      <p className="text-gray-600 mb-4">
        Status updates are broadcast in real-time as campaigns progress
      </p>

      {campaigns.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No campaigns found. Create one to get started.
        </div>
      ) : (
        <div className="space-y-2">
          {campaigns.map(campaign => (
            <CampaignCard 
              key={campaign.id}
              campaign={campaign}
              isUpdated={updatedCampaignIds.has(campaign.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Campaign Card Component
 * 
 * Displays a single campaign with its current status and stats.
 * Highlights itself when updated via WebSocket.
 */
function CampaignCard({ 
  campaign, 
  isUpdated 
}: { 
  campaign: Campaign; 
  isUpdated: boolean;
}) {
  const getStatusBg = (status: string) => {
    switch (status) {
      case 'DRAFT':
        return 'bg-gray-50 border-gray-200';
      case 'SCHEDULED':
        return 'bg-blue-50 border-blue-200';
      case 'SENDING':
        return 'bg-purple-50 border-purple-200';
      case 'SENT':
        return 'bg-green-50 border-green-200';
      case 'PAUSED':
        return 'bg-yellow-50 border-yellow-200';
      case 'CANCELLED':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'DRAFT':
        return 'text-gray-700 font-semibold';
      case 'SCHEDULED':
        return 'text-blue-700 font-semibold';
      case 'SENDING':
        return 'text-purple-700 font-semibold';
      case 'SENT':
        return 'text-green-700 font-semibold';
      case 'PAUSED':
        return 'text-yellow-700 font-semibold';
      case 'CANCELLED':
        return 'text-red-700 font-semibold';
      default:
        return 'text-gray-700 font-semibold';
    }
  };

  const deliveryRate = campaign.stats_total_recipients > 0
    ? ((campaign.stats_delivered / campaign.stats_total_recipients) * 100).toFixed(1)
    : 0;

  const openRate = campaign.stats_total_recipients > 0
    ? ((campaign.stats_opened / campaign.stats_total_recipients) * 100).toFixed(1)
    : 0;

  return (
    <div 
      className={`
        border-2 rounded-lg p-4 transition-all duration-300
        ${getStatusBg(campaign.status)}
        ${isUpdated ? 'ring-2 ring-green-500 shadow-lg' : ''}
      `}
    >
      <div className="flex items-start justify-between mb-2">
        <div>
          <h3 className="text-lg font-bold">{campaign.name}</h3>
          <p className="text-sm text-gray-600">{campaign.subject}</p>
        </div>
        <div className={`px-3 py-1 rounded-full text-xs ${getStatusText(campaign.status)}`}>
          {campaign.status}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-2 mb-3">
        <div className="text-center">
          <div className="text-2xl font-bold">{campaign.stats_sent}</div>
          <div className="text-xs text-gray-600">Sent</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold">{campaign.stats_delivered}</div>
          <div className="text-xs text-gray-600">Delivered</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold">{campaign.stats_opened}</div>
          <div className="text-xs text-gray-600">
            {openRate}% Open
          </div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold">{campaign.stats_clicked}</div>
          <div className="text-xs text-gray-600">Clicks</div>
        </div>
      </div>

      {/* Progress Bar */}
      {campaign.stats_total_recipients > 0 && (
        <div className="space-y-1">
          <div className="w-full bg-gray-300 rounded-full h-2 overflow-hidden">
            <div 
              className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-500"
              style={{
                width: `${(campaign.stats_sent / campaign.stats_total_recipients) * 100}%`
              }}
            />
          </div>
          <div className="text-xs text-gray-600">
            {campaign.stats_sent} / {campaign.stats_total_recipients} recipients
          </div>
        </div>
      )}

      {/* Last Updated */}
      <div className="text-xs text-gray-500 mt-2">
        Last updated: {campaign.updated_at 
          ? new Date(campaign.updated_at).toLocaleTimeString() 
          : 'Never'}
      </div>

      {/* Update Animation Indicator */}
      {isUpdated && (
        <div className="mt-2 text-xs text-green-600 font-semibold">
          ✓ Updated just now
        </div>
      )}
    </div>
  );
}
