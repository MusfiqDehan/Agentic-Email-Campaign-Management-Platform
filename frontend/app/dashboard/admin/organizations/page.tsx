'use client';

import { useCallback, useEffect, useState } from 'react';
import api from '@/config/axios';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Building2, Search, Users, Mail, TrendingUp, Power, PowerOff, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { formatDate } from '@/config/template-utils';

interface Organization {
  id: string;
  name: string;
  owner: {
    name: string;
    email: string;
  };
  member_count: number;
  template_count: number;
  campaign_count: number;
  created_at: string;
  is_active: boolean;
  deactivation_reason?: string;
  deactivated_at?: string;
}

export default function OrganizationsPage() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [isDeactivateDialogOpen, setIsDeactivateDialogOpen] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);
  const [deactivationReason, setDeactivationReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchOrganizations = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/campaigns/admin/organizations/');
      setOrganizations(response.data.data || []);
    } catch (error) {
      console.error(error);
      toast.error('Failed to fetch organizations');
      setOrganizations([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  const handleActivate = async (org: Organization) => {
    setIsSubmitting(true);
    try {
      await api.post(`/campaigns/admin/organizations/${org.id}/activate/`);
      toast.success(`${org.name} has been activated`);
      fetchOrganizations();
    } catch (error) {
      console.error(error);
      toast.error('Failed to activate organization');
    } finally {
      setIsSubmitting(false);
    }
  };

  const openDeactivateDialog = (org: Organization) => {
    setSelectedOrg(org);
    setDeactivationReason('');
    setIsDeactivateDialogOpen(true);
  };

  const handleDeactivate = async () => {
    if (!selectedOrg) return;
    
    setIsSubmitting(true);
    try {
      await api.post(`/campaigns/admin/organizations/${selectedOrg.id}/deactivate/`, {
        reason: deactivationReason || 'Deactivated by platform admin',
      });
      toast.success(`${selectedOrg.name} has been deactivated`);
      setIsDeactivateDialogOpen(false);
      setSelectedOrg(null);
      setDeactivationReason('');
      fetchOrganizations();
    } catch (error) {
      console.error(error);
      toast.error('Failed to deactivate organization');
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredOrganizations = organizations.filter(org =>
    org.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    org.owner.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    org.owner.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Organizations</h1>
        <p className="text-muted-foreground">
          Manage and monitor all organizations on the platform
        </p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Total Organizations
                </p>
                <h3 className="text-2xl font-bold mt-2">
                  {organizations.length}
                </h3>
              </div>
              <Building2 className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Active Organizations
                </p>
                <h3 className="text-2xl font-bold mt-2">
                  {organizations.filter(o => o.is_active).length}
                </h3>
              </div>
              <TrendingUp className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Total Members
                </p>
                <h3 className="text-2xl font-bold mt-2">
                  {organizations.reduce((sum, o) => sum + o.member_count, 0)}
                </h3>
              </div>
              <Users className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Total Campaigns
                </p>
                <h3 className="text-2xl font-bold mt-2">
                  {organizations.reduce((sum, o) => sum + o.campaign_count, 0)}
                </h3>
              </div>
              <Mail className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search organizations..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Organizations List */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto" />
            <p className="mt-4 text-muted-foreground">Loading organizations...</p>
          </div>
        ) : filteredOrganizations.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <Building2 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No organizations found</h3>
              <p className="text-muted-foreground">
                {searchQuery ? 'Try adjusting your search' : 'Organizations will appear here when created'}
              </p>
            </CardContent>
          </Card>
        ) : (
          filteredOrganizations.map((org) => (
            <Card key={org.id}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4 flex-1">
                    <div className="p-3 rounded-lg bg-primary/10">
                      <Building2 className="h-6 w-6 text-primary" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-lg font-semibold">{org.name}</h3>
                        <Badge variant={org.is_active ? 'default' : 'destructive'}>
                          {org.is_active ? 'Active' : 'Deactivated'}
                        </Badge>
                      </div>
                      {!org.is_active && org.deactivation_reason && (
                        <p className="text-sm text-destructive mb-2">
                          Reason: {org.deactivation_reason}
                        </p>
                      )}
                      <div className="grid grid-cols-2 gap-4 text-sm text-muted-foreground">
                        <div>
                          <p className="font-medium text-foreground mb-1">Owner</p>
                          <p>{org.owner.name}</p>
                          <p className="text-xs">{org.owner.email}</p>
                        </div>
                        <div>
                          <p className="font-medium text-foreground mb-1">Created</p>
                          <p>{formatDate(org.created_at)}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-6 mt-4 text-sm">
                        <div className="flex items-center gap-2">
                          <Users className="h-4 w-4 text-muted-foreground" />
                          <span>{org.member_count} members</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Mail className="h-4 w-4 text-muted-foreground" />
                          <span>{org.campaign_count} campaigns</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Building2 className="h-4 w-4 text-muted-foreground" />
                          <span>{org.template_count} templates</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {org.is_active ? (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openDeactivateDialog(org)}
                        className="text-destructive hover:text-destructive"
                      >
                        <PowerOff className="h-4 w-4 mr-1" />
                        Deactivate
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleActivate(org)}
                        disabled={isSubmitting}
                        className="text-green-600 hover:text-green-600"
                      >
                        {isSubmitting ? (
                          <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                        ) : (
                          <Power className="h-4 w-4 mr-1" />
                        )}
                        Activate
                      </Button>
                    )}
                    <Button variant="outline" size="sm">
                      View Details
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Deactivate Organization Dialog */}
      <Dialog open={isDeactivateDialogOpen} onOpenChange={setIsDeactivateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Deactivate Organization</DialogTitle>
            <DialogDescription>
              Are you sure you want to deactivate <strong>{selectedOrg?.name}</strong>?
              Users from this organization will not be able to login until it is reactivated.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="reason">Reason for deactivation</Label>
              <Textarea
                id="reason"
                placeholder="Enter a reason for deactivating this organization..."
                value={deactivationReason}
                onChange={(e) => setDeactivationReason(e.target.value)}
                rows={3}
              />
              <p className="text-xs text-muted-foreground">
                This reason will be shown to users when they try to login.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsDeactivateDialogOpen(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeactivate}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Deactivating...
                </>
              ) : (
                'Deactivate Organization'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
