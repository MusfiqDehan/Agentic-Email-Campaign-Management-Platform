'use client';

import { useEffect, useState } from 'react';
import api from '@/config/axios';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Building2, Search, Users, Mail, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';
import { formatDate } from '@/lib/template-utils';

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
}

export default function OrganizationsPage() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchOrganizations = async () => {
      setIsLoading(true);
      try {
        // This endpoint would need to be created in the backend
        const response = await api.get('/campaigns/admin/organizations/');
        setOrganizations(response.data.data || []);
      } catch (error) {
        console.error(error);
        toast.error('Failed to fetch organizations');
        // For now, show empty state
        setOrganizations([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchOrganizations();
  }, []);

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
                        <Badge variant={org.is_active ? 'default' : 'secondary'}>
                          {org.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </div>
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
                  <Button variant="outline" size="sm">
                    View Details
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
