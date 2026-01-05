'use client';

import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useRouter, useParams } from 'next/navigation';
import api from '@/config/axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { toast } from 'sonner';
import type { AxiosError } from 'axios';
import { ArrowLeft, Loader2 } from 'lucide-react';
import Link from 'next/link';

const providerSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  provider_type: z.enum(['SMTP', 'AWS_SES', 'SENDGRID', 'BREVO']),
  is_default: z.boolean(),
  is_active: z.boolean(),
  auto_health_check: z.boolean(),
  // Config fields
  smtp_server: z.string().optional(),
  smtp_port: z.string().optional(),
  smtp_username: z.string().optional(),
  smtp_password: z.string().optional(),
  from_email: z.string().min(1, 'From email is required').email('Invalid email'),
  use_tls: z.boolean().optional(),
  use_ssl: z.boolean().optional(),

  aws_access_key_id: z.string().optional(),
  aws_secret_access_key: z.string().optional(),
  aws_session_token: z.string().optional(),
  region_name: z.string().optional(),

  api_key: z.string().optional(), // For SendGrid/Brevo
});

type ProviderFormValues = z.infer<typeof providerSchema>;
type ProviderType = ProviderFormValues['provider_type'];

export default function EditProviderPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [providerType, setProviderType] = useState<ProviderType>('SMTP');

  const { register, handleSubmit, setValue, reset, formState: { errors } } = useForm<ProviderFormValues>({
    resolver: zodResolver(providerSchema),
    defaultValues: {
      provider_type: 'SMTP',
      is_active: true,
      auto_health_check: true,
      use_tls: true,
      use_ssl: false,
      is_default: false,
      name: '',
      from_email: '',
      smtp_server: '',
      smtp_port: '',
      smtp_username: '',
      smtp_password: '',
      aws_access_key_id: '',
      aws_secret_access_key: '',
      aws_session_token: '',
      region_name: '',
      api_key: '',
    }
  });

  useEffect(() => {
    const fetchProvider = async () => {
      try {
        const response = await api.get(`/campaigns/org/providers/${id}/`);
        const provider = response.data.data;
        const config = provider.config || {};
        
        setProviderType(provider.provider_type);
        
        reset({
          name: provider.name,
          provider_type: provider.provider_type,
          is_default: provider.is_default,
          is_active: provider.is_active,
          auto_health_check: false, // Don't auto-check on load
          from_email: config.from_email || '',
          // SMTP
          smtp_server: config.smtp_server || '',
          smtp_port: config.smtp_port?.toString() || '',
          smtp_username: config.username || '',
          smtp_password: '', // Don't populate password for security
          use_tls: config.use_tls ?? true,
          use_ssl: config.use_ssl ?? false,
          // AWS
          aws_access_key_id: config.aws_access_key_id || '',
          aws_secret_access_key: '', // Don't populate secret
          aws_session_token: '',
          region_name: config.region_name || '',
          // API Key based
          api_key: '', // Don't populate API key
        });
      } catch (error) {
        console.error(error);
        toast.error('Failed to fetch provider details');
        router.push('/dashboard/settings/providers');
      } finally {
        setIsLoading(false);
      }
    };

    if (id) fetchProvider();
  }, [id, reset, router]);

  const onSubmit = async (data: ProviderFormValues) => {
    setIsSaving(true);
    try {
      let config: Record<string, unknown> = {};

      if (data.provider_type === 'SMTP') {
        config = {
          smtp_server: data.smtp_server,
          smtp_port: parseInt(data.smtp_port || '587'),
          username: data.smtp_username,
          from_email: data.from_email,
          use_tls: data.use_tls,
          use_ssl: data.use_ssl,
        };
        if (data.smtp_password) config.password = data.smtp_password;
      } else if (data.provider_type === 'AWS_SES') {
        config = {
          aws_access_key_id: data.aws_access_key_id,
          region_name: data.region_name,
          from_email: data.from_email,
        };
        if (data.aws_secret_access_key) config.aws_secret_access_key = data.aws_secret_access_key;
        if (data.aws_session_token) config.aws_session_token = data.aws_session_token;
      } else if (['SENDGRID', 'BREVO'].includes(data.provider_type)) {
        config = {
          from_email: data.from_email
        };
        if (data.api_key) config.api_key = data.api_key;
      }

      const payload = {
        name: data.name,
        provider_type: data.provider_type,
        is_default: data.is_default,
        is_active: data.is_active,
        auto_health_check: data.auto_health_check,
        config: config,
      };

      await api.patch(`/campaigns/org/providers/${id}/`, payload);
      toast.success('Provider updated successfully');
      router.push('/dashboard/settings/providers');
    } catch (error: unknown) {
      console.error('API Error:', error);
      const axiosError = error as AxiosError<{ detail?: string; error?: string }>;
      toast.error(axiosError.response?.data?.detail || axiosError.response?.data?.error || 'Failed to update provider');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/settings/providers">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Edit Provider</h2>
          <p className="text-muted-foreground">Update your email provider configuration.</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Provider Details</CardTitle>
          <CardDescription>Modify the configuration details for your email provider.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="name">Provider Name</Label>
              <Input id="name" placeholder="e.g., Corporate Gmail" {...register('name')} />
              {errors.name && <p className="text-sm text-red-500">{errors.name.message}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="provider_type">Provider Type</Label>
              <Select
                onValueChange={(val) => {
                  const typed = val as ProviderType;
                  setValue('provider_type', typed);
                  setProviderType(typed);
                }}
                value={providerType}
                disabled
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select provider type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="SMTP">SMTP</SelectItem>
                  <SelectItem value="AWS_SES">Amazon SES</SelectItem>
                  <SelectItem value="SENDGRID">SendGrid</SelectItem>
                  <SelectItem value="BREVO">Brevo</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">Provider type cannot be changed after creation.</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="from_email">From Email</Label>
              <Input id="from_email" placeholder="sender@example.com" {...register('from_email')} />
              {errors.from_email && <p className="text-sm text-red-500">{errors.from_email.message}</p>}
            </div>

            {providerType === 'SMTP' && (
              <div className="space-y-4 rounded-xl border p-4 bg-muted/50">
                <h3 className="font-medium">SMTP Configuration</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="smtp_server">SMTP Host</Label>
                    <Input id="smtp_server" placeholder="smtp.gmail.com" {...register('smtp_server')} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="smtp_port">Port</Label>
                    <Input id="smtp_port" placeholder="587" {...register('smtp_port')} />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="smtp_username">Username</Label>
                  <Input id="smtp_username" {...register('smtp_username')} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="smtp_password">Password (Leave blank to keep current)</Label>
                  <Input id="smtp_password" type="password" {...register('smtp_password')} />
                </div>
                <div className="flex gap-6">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="use_tls"
                      onCheckedChange={(checked) => setValue('use_tls', checked as boolean)}
                      defaultChecked={true}
                    />
                    <Label htmlFor="use_tls">Use TLS</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="use_ssl"
                      onCheckedChange={(checked) => setValue('use_ssl', checked as boolean)}
                    />
                    <Label htmlFor="use_ssl">Use SSL</Label>
                  </div>
                </div>
              </div>
            )}

            {providerType === 'AWS_SES' && (
              <div className="space-y-4 rounded-xl border p-4 bg-muted/50">
                <h3 className="font-medium">AWS SES Configuration</h3>
                <div className="space-y-2">
                  <Label htmlFor="aws_access_key_id">Access Key ID</Label>
                  <Input id="aws_access_key_id" {...register('aws_access_key_id')} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="aws_secret_access_key">Secret Access Key (Leave blank to keep current)</Label>
                  <Input id="aws_secret_access_key" type="password" {...register('aws_secret_access_key')} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="aws_session_token">Session Token (Optional)</Label>
                  <Input id="aws_session_token" type="password" {...register('aws_session_token')} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="region_name">Region</Label>
                  <Input id="region_name" placeholder="us-east-1" {...register('region_name')} />
                </div>
              </div>
            )}

            {['SENDGRID', 'BREVO'].includes(providerType) && (
              <div className="space-y-4 rounded-xl border p-4 bg-muted/50">
                <h3 className="font-medium">API Configuration</h3>
                <div className="space-y-2">
                  <Label htmlFor="api_key">API Key (Leave blank to keep current)</Label>
                  <Input id="api_key" type="password" {...register('api_key')} />
                </div>
              </div>
            )}

            <div className="flex flex-col gap-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_default"
                  onCheckedChange={(checked) => setValue('is_default', checked as boolean)}
                  defaultChecked={false}
                />
                <Label htmlFor="is_default">Set as default provider</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_active"
                  onCheckedChange={(checked) => setValue('is_active', checked as boolean)}
                  defaultChecked={true}
                />
                <Label htmlFor="is_active">Provider is active</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="auto_health_check"
                  onCheckedChange={(checked) => setValue('auto_health_check', checked as boolean)}
                />
                <Label htmlFor="auto_health_check">Run health check on save</Label>
              </div>
            </div>

            <Button type="submit" className="w-full bg-gradient-to-r from-primary to-blue-600 hover:opacity-90" disabled={isSaving}>
              {isSaving ? 'Saving...' : 'Update Provider'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
