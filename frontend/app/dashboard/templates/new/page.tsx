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
import Editor from '@/components/editor';

const templateSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  subject: z.string().optional(),
  content: z.string().min(1, 'Content is required'),
});

type TemplateFormValues = z.infer<typeof templateSchema>;

export default function NewTemplatePage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<TemplateFormValues>({
    resolver: zodResolver(templateSchema),
  });

  const content = watch('content');

  const onSubmit = async (data: TemplateFormValues) => {
    setIsLoading(true);
    try {
      await api.post('/campaigns/email-templates/', {
        name: data.name,
        subject: data.subject,
        html_content: data.content,
      });
      toast.success('Template created successfully');
      router.push('/dashboard/templates');
    } catch (error: any) {
      console.error(error);
      toast.error(error.response?.data?.detail || 'Failed to create template');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/templates">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Create Template</h2>
          <p className="text-muted-foreground">Design your email content.</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Template Details</CardTitle>
          <CardDescription>Configure the basic details and content of your template.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="name">Template Name</Label>
                <Input id="name" placeholder="e.g., Monthly Newsletter" {...register('name')} />
                {errors.name && <p className="text-sm text-red-500">{errors.name.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="subject">Default Subject (Optional)</Label>
                <Input id="subject" placeholder="e.g., Check out our latest news" {...register('subject')} />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Email Content</Label>
              <Editor 
                value={content || ''} 
                onChange={(val) => setValue('content', val)} 
                placeholder="Start typing your email content..."
              />
              {errors.content && <p className="text-sm text-red-500">{errors.content.message}</p>}
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Saving...' : 'Save Template'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
