'use client';

import { useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useRouter } from 'next/navigation';
import api from '@/lib/axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { ArrowLeft, Sparkles, Loader2 } from 'lucide-react';
import Link from 'next/link';
import Editor from '@/components/editor';

const templateSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  subject: z.string().min(1, 'Subject is required'),
  content: z.string().min(1, 'Content is required'),
  category: z.string().min(1, 'Category is required'),
  preview_text: z.string().optional(),
  description: z.string().optional(),
  tags: z.string().optional(),
  text_body: z.string().optional(),
});

type TemplateFormValues = z.infer<typeof templateSchema>;

const CATEGORIES = [
  { value: 'NEWSLETTER', label: 'Newsletter' },
  { value: 'PROMOTIONAL', label: 'Promotional' },
  { value: 'ANNOUNCEMENT', label: 'Announcement' },
  { value: 'WELCOME', label: 'Welcome' },
  { value: 'EMAIL_VERIFICATION', label: 'Email Verification' },
  { value: 'PASSWORD_RESET', label: 'Password Reset' },
  { value: 'INVITATION', label: 'Invitation' },
  { value: 'REMINDER', label: 'Reminder' },
  { value: 'NOTIFICATION', label: 'Notification' },
  { value: 'SUBSCRIPTION_CONFIRMATION', label: 'Subscription Confirmation' },
  { value: 'SUBSCRIPTION_RENEWAL', label: 'Subscription Renewal' },
  { value: 'OTHER', label: 'Other' },
];

export default function NewTemplatePage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const { register, handleSubmit, setValue, watch, control, formState: { errors } } = useForm<TemplateFormValues>({
    resolver: zodResolver(templateSchema),
    defaultValues: {
      category: 'OTHER',
      name: '',
      subject: '',
      content: '',
      preview_text: '',
      description: '',
      tags: '',
      text_body: '',
    }
  });

  const content = watch('content');
  const subject = watch('subject');
  const name = watch('name');

  const handleGenerateAI = async () => {
    if (!name || !subject) {
      toast.error('Please enter Template Name and Subject first');
      return;
    }

    setIsGenerating(true);
    try {
      const response = await api.post('/campaigns/ai/generate/email/content/', {
        template_name: name,
        email_subject: subject,
      });

      const { email_body, text_body, description, tags } = response.data;

      if (email_body) setValue('content', email_body);
      if (text_body) setValue('text_body', text_body);
      if (description) setValue('description', description);
      if (tags && Array.isArray(tags)) setValue('tags', tags.join(', '));

      toast.success('AI content generated successfully');
    } catch (error: any) {
      console.error(error);
      toast.error(error.response?.data?.error || 'Failed to generate AI content');
    } finally {
      setIsGenerating(false);
    }
  };

  const onSubmit = async (data: TemplateFormValues) => {
    setIsLoading(true);
    try {
      const tagsArray = data.tags ? data.tags.split(',').map(tag => tag.trim()).filter(tag => tag !== '') : [];

      await api.post('/campaigns/templates/', {
        template_name: data.name,
        email_subject: data.subject,
        email_body: data.content,
        category: data.category,
        preview_text: data.preview_text,
        description: data.description,
        tags: tagsArray,
        text_body: data.text_body,
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
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Template Details</CardTitle>
              <CardDescription>Configure the basic details and content of your template.</CardDescription>
            </div>
          </div>
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
                <Label htmlFor="category">Category</Label>
                <Controller
                  name="category"
                  control={control}
                  render={({ field }) => (
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a category" />
                      </SelectTrigger>
                      <SelectContent>
                        {CATEGORIES.map((cat) => (
                          <SelectItem key={cat.value} value={cat.value}>
                            {cat.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="subject">Default Subject</Label>
                <Input id="subject" placeholder="e.g., Check out our latest news" {...register('subject')} />
                {errors.subject && <p className="text-sm text-red-500">{errors.subject.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="preview_text">Preview Text</Label>
                <Input id="preview_text" placeholder="Short preview text" {...register('preview_text')} />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Internal Description</Label>
              <Textarea
                id="description"
                placeholder="What is this template for?"
                {...register('description')}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="tags">Tags (comma separated)</Label>
              <Input id="tags" placeholder="marketing, newsletter, summer" {...register('tags')} />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Email Content (HTML)</Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleGenerateAI}
                  disabled={isGenerating}
                  className="gap-2"
                >
                  {isGenerating ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Sparkles className="h-4 w-4 text-purple-500" />
                  )}
                  {isGenerating ? 'Generating...' : 'Generate with AI'}
                </Button>
              </div>
              <Editor
                value={content || ''}
                onChange={(val) => setValue('content', val)}
                placeholder="Start typing your email content..."
              />
              {errors.content && <p className="text-sm text-red-500">{errors.content.message}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="text_body">Plain Text Body (Fallback)</Label>
              <Textarea
                id="text_body"
                placeholder="Plain text version of your email..."
                className="min-h-[150px]"
                {...register('text_body')}
              />
            </div>

            <Button type="submit" className="w-full bg-gradient-to-r from-primary to-blue-600 hover:opacity-90" disabled={isLoading}>
              {isLoading ? 'Saving...' : 'Save Template'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
