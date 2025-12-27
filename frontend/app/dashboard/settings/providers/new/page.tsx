'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useRouter } from 'next/navigation';
import api from '@/lib/axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { toast } from 'sonner';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';

const providerSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  provider_type: z.enum(['SMTP', 'AWS_SES', 'SENDGRID', 'BREVO']),
  is_default: z.boolean().default(false),
  is_active: z.boolean().default(true),
  auto_health_check: z.boolean().default(true),
  // Config fields will be validated manually or via refinement based on type
  smtp_server: z.string().optional(),
  smtp_port: z.string().optional(), // Input is string, convert to number
  smtp_username: z.string().optional(),
  smtp_password: z.string().optional(),
  from_email: z.string().email('Invalid email').optional(),
  use_tls: z.boolean().optional(),
  use_ssl: z.boolean().optional(),
  
  aws_access_key_id: z.string().optional(),
  aws_secret_access_key: z.string().optional(),
  region_name: z.string().optional(),
  
  api_key: z.string().optional(), // For SendGrid/Brevo
});

type ProviderFormValues = z.infer<typeof providerSchema>;

export default function NewProviderPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [providerType, setProviderType] = useState<string>('SMTP');

  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm({
    resolver: zodResolver(providerSchema),
    defaultValues: {
      provider_type: 'SMTP',
      is_active: true,
      auto_health_check: true,
      use_tls: true,
      use_ssl: false,
    }
  });

  const onSubmit = async (data: ProviderFormValues) => {
    setIsLoading(true);
    try {
      let config: any = {};

      if (data.provider_type === 'SMTP') {
        if (!data.smtp_server || !data.smtp_port || !data.smtp_username || !data.smtp_password || !data.from_email) {
          toast.error('Please fill all SMTP fields');
          setIsLoading(false);
          return;
        }
        config = {
          smtp_server: data.smtp_server,
          smtp_port: parseInt(data.smtp_port),
          username: data.smtp_username,
          password: data.smtp_password,
          from_email: data.from_email,
          use_tls: data.use_tls,
          use_ssl: data.use_ssl,
        };
      } else if (data.provider_type === 'AWS_SES') {
        if (!data.aws_access_key_id || !data.aws_secret_access_key || !data.region_name || !data.from_email) {
          toast.error('Please fill all AWS SES fields');
          setIsLoading(false);
          return;
        }
        config = {
          aws_access_key_id: data.aws_access_key_id,
          aws_secret_access_key: data.aws_secret_access_key,
          region_name: data.region_name,
          from_email: data.from_email,
        };
      } else if (['SENDGRID', 'BREVO'].includes(data.provider_type)) {
         if (!data.api_key || !data.from_email) {
          toast.error('Please fill all API fields');
          setIsLoading(false);
          return;
        }
        config = {
            api_key: data.api_key,
            from_email: data.from_email
        }
      }

      const payload = {
        name: data.name,
        provider_type: data.provider_type,
        is_default: data.is_default,
        is_active: data.is_active,
        auto_health_check: data.auto_health_check,
        config: config,
      };

      await api.post('/campaigns/organization-providers/', payload);
      toast.success('Provider created successfully');
      router.push('/dashboard/settings/providers');
    } catch (error: any) {
      console.error(error);
      toast.error(error.response?.data?.detail || 'Failed to create provider');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/settings/providers">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Add Provider</h2>
          <p className="text-muted-foreground">Configure a new email sending service.</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Provider Details</CardTitle>
          <CardDescription>Enter the configuration details for your email provider.</CardDescription>
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
                  setValue('provider_type', val as any);
                  setProviderType(val);
                }} 
                defaultValue="SMTP"
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
            </div>

            <div className="space-y-2">
              <Label htmlFor="from_email">From Email</Label>
              <Input id="from_email" placeholder="sender@example.com" {...register('from_email')} />
              <p className="text-xs text-muted-foreground">The email address that will appear as the sender.</p>
            </div>

            {providerType === 'SMTP' && (
              <div className="space-y-4 rounded-md border p-4 bg-gray-50">
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
                  <Label htmlFor="smtp_password">Password</Label>
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
              <div className="space-y-4 rounded-md border p-4 bg-gray-50">
                <h3 className="font-medium">AWS SES Configuration</h3>
                <div className="space-y-2">
                  <Label htmlFor="aws_access_key_id">Access Key ID</Label>
                  <Input id="aws_access_key_id" {...register('aws_access_key_id')} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="aws_secret_access_key">Secret Access Key</Label>
                  <Input id="aws_secret_access_key" type="password" {...register('aws_secret_access_key')} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="region_name">Region</Label>
                  <Input id="region_name" placeholder="us-east-1" {...register('region_name')} />
                </div>
              </div>
            )}

            {['SENDGRID', 'BREVO'].includes(providerType) && (
               <div className="space-y-4 rounded-md border p-4 bg-gray-50">
                <h3 className="font-medium">API Configuration</h3>
                <div className="space-y-2">
                  <Label htmlFor="api_key">API Key</Label>
                  <Input id="api_key" type="password" {...register('api_key')} />
                </div>
               </div>
            )}

            <div className="flex flex-col gap-3">
               <div className="flex items-center space-x-2">
                <Checkbox 
                    id="is_default" 
                    onCheckedChange={(checked) => setValue('is_default', checked as boolean)}
                />
                <Label htmlFor="is_default">Set as default provider</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox 
                    id="auto_health_check" 
                    onCheckedChange={(checked) => setValue('auto_health_check', checked as boolean)}
                    defaultChecked={true}
                />
                <Label htmlFor="auto_health_check">Run health check on save</Label>
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Saving...' : 'Save Provider'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
