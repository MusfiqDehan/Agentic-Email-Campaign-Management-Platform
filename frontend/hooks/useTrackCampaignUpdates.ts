import { useState, useEffect, useCallback } from 'react';
import { useRealtimeUpdates, CampaignStatusUpdate } from './useRealtimeUpdates';
import { Campaign } from '@/services/campaigns';

/**
 * Hook to track real-time campaign status updates
 * 
 * Usage:
 * const { campaigns, updateCampaign } = useTrackCampaignUpdates([initialCampaigns]);
 * 
 * @param initialCampaigns - Array of campaigns to track
 * @param onUpdate - Optional callback when a campaign is updated
 */
export const useTrackCampaignUpdates = (
  initialCampaigns: Campaign[] = [],
  onUpdate?: (campaign: Campaign) => void
) => {
  const [campaigns, setCampaigns] = useState<Campaign[]>(initialCampaigns);
  const { onCampaignStatusUpdate } = useRealtimeUpdates();

  // Handle status update from WebSocket
  const handleStatusUpdate = useCallback((update: CampaignStatusUpdate) => {
    setCampaigns(prev => 
      prev.map(campaign => {
        if (campaign.id === update.id) {
          const updatedCampaign = {
            ...campaign,
            status: update.status,
            stats_sent: update.stats_sent,
            stats_delivered: update.stats_delivered,
            stats_opened: update.stats_opened,
            stats_clicked: update.stats_clicked,
            stats_total_recipients: update.stats_total_recipients,
            updated_at: update.updated_at
          };
          
          // Call optional callback
          if (onUpdate) {
            onUpdate(updatedCampaign);
          }
          
          return updatedCampaign;
        }
        return campaign;
      })
    );
  }, [onUpdate]);

  // Subscribe to all campaign updates
  useEffect(() => {
    // Subscribe to global campaign updates (using '*' as key)
    const unsubscribe = onCampaignStatusUpdate('*', handleStatusUpdate);
    
    return unsubscribe;
  }, [onCampaignStatusUpdate, handleStatusUpdate]);

  // Update initial campaigns when they change
  useEffect(() => {
    setCampaigns(initialCampaigns);
  }, [initialCampaigns]);

  const updateCampaign = useCallback((campaignId: string, updates: Partial<Campaign>) => {
    setCampaigns(prev =>
      prev.map(campaign =>
        campaign.id === campaignId
          ? { ...campaign, ...updates }
          : campaign
      )
    );
  }, []);

  return {
    campaigns,
    updateCampaign,
    setCampaigns
  };
};
