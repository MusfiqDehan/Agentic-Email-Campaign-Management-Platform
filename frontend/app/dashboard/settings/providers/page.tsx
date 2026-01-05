'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/config/axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus, Trash2, CheckCircle, XCircle, RefreshCw, AlertTriangle, Edit2, Eye } from 'lucide-react';
import { toast } from 'sonner';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface Provider {
  id: string;
  name: string;
  provider_type: string;
  is_default: boolean;
  health_status: string;
  health_details: string;
  emails_sent_today: number;
  is_active: boolean;
  priority: number;
  max_emails_per_day: number;
  created_at: string;
}

export default function ProvidersPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [providerToDelete, setProviderToDelete] = useState<string | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<Provider | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  const fetchProviders = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/campaigns/org/providers/');
      setProviders(response.data.data || []);
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

  const handleDeleteClick = (id: string) => {
    setProviderToDelete(id);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!providerToDelete) return;
    try {
      await api.delete(`/campaigns/org/providers/${providerToDelete}/`);
      toast.success('Provider deleted');
      fetchProviders();
    } catch (error) {
      console.error(error);
      toast.error('Failed to delete provider');
    } finally {
      setDeleteDialogOpen(false);
      setProviderToDelete(null);
    }
  };

  const handleHealthCheck = async (id: string) => {
    try {
      await api.post(`/campaigns/org/providers/${id}/health-check/`);
      toast.success('Health check initiated');
      fetchProviders();
    } catch (error) {
      console.error(error);
      toast.error('Health check failed');
    }
  };

  const handleViewDetails = (provider: Provider) => {
    setSelectedProvider(provider);
    setDetailsOpen(true);
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
                <div className="flex gap-1">
                  <Button variant="ghost" size="icon" onClick={() => handleViewDetails(provider)} title="View Details">
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Link href={`/dashboard/settings/providers/${provider.id}/edit`}>
                    <Button variant="ghost" size="icon" title="Edit Provider">
                      <Edit2 className="h-4 w-4" />
                    </Button>
                  </Link>
                  <Button variant="ghost" size="icon" onClick={() => handleHealthCheck(provider.id)} title="Refresh Health">
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon" className="text-destructive" onClick={() => handleDeleteClick(provider.id)}>
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
                    <div className="mt-2 rounded bg-muted p-2 text-xs text-muted-foreground line-clamp-2">
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

      {/* Details Dialog */}
      <Dialog open={detailsOpen} onOpenChange={setDetailsOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Provider Details</DialogTitle>
            <DialogDescription>
              Full configuration and status for {selectedProvider?.name}
            </DialogDescription>
          </DialogHeader>
          {selectedProvider && (
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Type</p>
                  <p className="font-medium">{selectedProvider.provider_type}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Status</p>
                  <p className={`font-medium ${selectedProvider.health_status === 'HEALTHY' ? 'text-green-600' : 'text-red-600'}`}>
                    {selectedProvider.health_status}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Priority</p>
                  <p className="font-medium">{selectedProvider.priority}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Daily Limit</p>
                  <p className="font-medium">{selectedProvider.max_emails_per_day}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Active</p>
                  <p className="font-medium">{selectedProvider.is_active ? 'Yes' : 'No'}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Created At</p>
                  <p className="font-medium">{new Date(selectedProvider.created_at).toLocaleDateString()}</p>
                </div>
              </div>
              {selectedProvider.health_details && (
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Health Details</p>
                  <div className="rounded-md bg-muted p-3 text-xs font-mono">
                    {selectedProvider.health_details}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
                <AlertTriangle className="h-6 w-6 text-destructive" />
              </div>
              <div>
                <AlertDialogTitle>Delete Provider</AlertDialogTitle>
                <AlertDialogDescription>
                  Are you sure you want to delete this provider? This action cannot be undone.
                </AlertDialogDescription>
              </div>
            </div>
          </AlertDialogHeader>
          <AlertDialogFooter className="mt-4">
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleDeleteConfirm}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
