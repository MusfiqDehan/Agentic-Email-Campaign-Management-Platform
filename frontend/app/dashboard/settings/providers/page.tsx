'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus, Trash2, CheckCircle, XCircle, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

interface Provider {
  id: string;
  name: string;
  provider_type: string;
  is_default: boolean;
  health_status: string;
  health_details: string;
  emails_sent_today: number;
}

export default function ProvidersPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchProviders = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/campaigns/organization-providers/');
      setProviders(response.data);
    } catch (error) {
      console.error(error);
      toast.error('Failed to fetch providers');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProviders();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this provider?')) return;
    try {
      await api.delete(`/campaigns/organization-providers/${id}/`);
      toast.success('Provider deleted');
      fetchProviders();
    } catch (error) {
      console.error(error);
      toast.error('Failed to delete provider');
    }
  };

  const handleHealthCheck = async (id: string) => {
    try {
      await api.post(`/campaigns/organization-providers/${id}/health_check/`);
      toast.success('Health check initiated');
      fetchProviders();
    } catch (error) {
      console.error(error);
      toast.error('Health check failed');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Email Providers</h2>
          <p className="text-muted-foreground">Manage your email sending services.</p>
        </div>
        <Link href="/dashboard/settings/providers/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" /> Add Provider
          </Button>
        </Link>
      </div>

      {isLoading ? (
        <div>Loading...</div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {providers.map((provider) => (
            <Card key={provider.id}>
              <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                <div className="space-y-1">
                  <CardTitle className="text-base font-medium">
                    {provider.name}
                    {provider.is_default && (
                      <span className="ml-2 rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                        Default
                      </span>
                    )}
                  </CardTitle>
                  <CardDescription>{provider.provider_type}</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button variant="ghost" size="icon" onClick={() => handleHealthCheck(provider.id)} title="Check Health">
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon" className="text-destructive" onClick={() => handleDelete(provider.id)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="mt-4 space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Status</span>
                    <div className="flex items-center gap-1">
                      {provider.health_status === 'HEALTHY' ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-500" />
                      )}
                      <span>{provider.health_status}</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Sent Today</span>
                    <span>{provider.emails_sent_today}</span>
                  </div>
                  {provider.health_details && (
                    <div className="mt-2 rounded bg-muted p-2 text-xs text-muted-foreground">
                      {provider.health_details}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
          {providers.length === 0 && (
            <div className="col-span-full flex h-32 items-center justify-center rounded-lg border border-dashed">
              <p className="text-muted-foreground">No providers configured.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
