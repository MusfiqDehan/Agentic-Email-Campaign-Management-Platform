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
import { toast } from 'sonner';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';

const listSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
});

type ListFormValues = z.infer<typeof listSchema>;

export default function NewContactListPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<ListFormValues>({
    resolver: zodResolver(listSchema),
  });

  const onSubmit = async (data: ListFormValues) => {
    setIsLoading(true);
    try {
      await api.post('/campaigns/contact-lists/', data);
      toast.success('Contact list created successfully');
      router.push('/dashboard/contacts');
    } catch (error: any) {
      console.error(error);
      toast.error(error.response?.data?.detail || 'Failed to create list');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-md mx-auto">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/contacts">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h2 className="text-3xl font-bold tracking-tight">New List</h2>
          <p className="text-muted-foreground">Create a new segment for your contacts.</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>List Details</CardTitle>
          <CardDescription>Give your contact list a name.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">List Name</Label>
              <Input id="name" placeholder="e.g., Newsletter Subscribers" {...register('name')} />
              {errors.name && <p className="text-sm text-red-500">{errors.name.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description (Optional)</Label>
              <Input id="description" placeholder="e.g., Users who signed up via website" {...register('description')} />
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Creating...' : 'Create List'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
