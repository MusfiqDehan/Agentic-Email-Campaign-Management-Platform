'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { Loader2, ArrowLeft, Save, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

import api from '@/config/axios';
import { TEMPLATE_CATEGORIES } from '@/config/constants';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { getCategoryInfo, getApprovalStatusInfo, formatVersion } from '@/config/template-utils';

interface TemplateFormState {
  name: string;
  subject: string;
  category: string;
  preview_text: string;
  description: string;
  body_html: string;
  body_text: string;
}

interface TemplateData {
  id: string;
  template_name: string;
  email_subject: string;
  email_body: string;
  text_body: string;
  category: string;
  preview_text: string;
  description: string;
  is_global: boolean;
  approval_status: string;
  version: number;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

const DEFAULT_CATEGORY = TEMPLATE_CATEGORIES[0]?.value ?? 'welcome';

export default function EditTemplatePage() {
  const params = useParams();
  const router = useRouter();
  const templateId = params.id as string;

  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [templateData, setTemplateData] = useState<TemplateData | null>(null);
  const [formState, setFormState] = useState<TemplateFormState>({
    name: '',
    subject: '',
    category: DEFAULT_CATEGORY,
    preview_text: '',
    description: '',
    body_html: '',
    body_text: '',
  });

  // Fetch template data
  useEffect(() => {
    const fetchTemplate = async () => {
      setIsLoading(true);
      try {
        const response = await api.get(`/campaigns/admin/templates/${templateId}/`);
        const template = response.data.data;
        setTemplateData(template);
        setFormState({
          name: template.template_name || '',
          subject: template.email_subject || '',
          category: template.category?.toLowerCase() || DEFAULT_CATEGORY,
          preview_text: template.preview_text || '',
          description: template.description || '',
          body_html: template.email_body || '',
          body_text: template.text_body || '',
        });
      } catch (error) {
        console.error(error);
        toast.error('Failed to fetch template');
        router.push('/dashboard/admin/templates');
      } finally {
        setIsLoading(false);
      }
    };

    if (templateId) {
      fetchTemplate();
    }
  }, [templateId, router]);

  const isFormValid = useMemo(() => {
    return (
      formState.name.trim().length > 0 &&
      formState.subject.trim().length > 0 &&
      formState.body_html.trim().length > 0
    );
  }, [formState]);

  const handleChange = (field: keyof TemplateFormState, value: string) => {
    setFormState((prev) => ({ ...prev, [field]: value }));
  };

  const handleGenerateAI = async () => {
    if (!formState.name || !formState.subject) {
      toast.error('Please enter Template Name and Subject first');
      return;
    }

    setIsGenerating(true);
    try {
      const response = await api.post('/campaigns/ai/generate/email/content/', {
        template_name: formState.name,
        email_subject: formState.subject,
      });

      const { email_body, text_body, description } = response.data;

      if (email_body) handleChange('body_html', email_body);
      if (text_body) handleChange('body_text', text_body);
      if (description) handleChange('description', description);

      toast.success('AI content generated successfully');
    } catch (error: any) {
      console.error(error);
      toast.error(error?.response?.data?.error || 'Failed to generate AI content');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!isFormValid) {
      toast.error('Please complete all required fields.');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        template_name: formState.name.trim(),
        email_subject: formState.subject.trim(),
        email_body: formState.body_html,
        text_body: formState.body_text,
        category: formState.category.toUpperCase(),
        preview_text: formState.preview_text,
        description: formState.description,
      };

      await api.patch(`/campaigns/admin/templates/${templateId}/`, payload);

      toast.success('Template updated successfully.');
      router.push('/dashboard/admin/templates');
      router.refresh();
    } catch (error: any) {
      console.error(error);
      const detail = error?.response?.data?.detail;
      toast.error(detail ?? 'Failed to update template');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto" />
            <p className="mt-4 text-muted-foreground">Loading template...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground flex items-center gap-2">
            <ArrowLeft className="h-4 w-4" />
            <Link href="/dashboard/admin/templates" className="hover:underline">
              Back to Templates
            </Link>
          </p>
          <h1 className="text-3xl font-bold mt-2">Edit Template</h1>
          <p className="text-muted-foreground">
            Update the content and metadata for this template.
          </p>
        </div>
        {templateData && (
          <div className="flex items-center gap-2">
            <Badge variant={templateData.is_global ? "default" : "secondary"}>
              {templateData.is_global ? "Global" : "Organization"}
            </Badge>
            <Badge variant="outline">{formatVersion(templateData.version)}</Badge>
            <Badge className={getApprovalStatusInfo(templateData.approval_status).color}>
              {getApprovalStatusInfo(templateData.approval_status).label}
            </Badge>
          </div>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Template Details</CardTitle>
          <CardDescription>
            {templateData && `Last updated: ${new Date(templateData.updated_at).toLocaleDateString()}`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label htmlFor="name">Template Name *</Label>
                <Input
                  id="name"
                  value={formState.name}
                  onChange={(event) => handleChange('name', event.target.value)}
                  placeholder="Onboarding Welcome"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="subject">Email Subject *</Label>
                <Input
                  id="subject"
                  value={formState.subject}
                  onChange={(event) => handleChange('subject', event.target.value)}
                  placeholder="Welcome to the platform"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="category">Category *</Label>
                <Select
                  value={formState.category}
                  onValueChange={(value) => handleChange('category', value)}
                >
                  <SelectTrigger id="category">
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    {TEMPLATE_CATEGORIES.map((category) => (
                      <SelectItem key={category.value} value={category.value}>
                        <span className="mr-2">{category.icon}</span>
                        {category.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="preview_text">Preview Text</Label>
                <Input
                  id="preview_text"
                  value={formState.preview_text}
                  onChange={(event) => handleChange('preview_text', event.target.value)}
                  placeholder="Short summary displayed in email clients"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                rows={2}
                value={formState.description}
                onChange={(event) => handleChange('description', event.target.value)}
                placeholder="Internal description for this template"
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="body_html">HTML Body *</Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleGenerateAI}
                  disabled={isGenerating || !formState.name || !formState.subject}
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
              <Textarea
                id="body_html"
                rows={12}
                value={formState.body_html}
                onChange={(event) => handleChange('body_html', event.target.value)}
                placeholder="<h1>Hello {{ first_name }}</h1>"
                required
              />
              <p className="text-xs text-muted-foreground">
                Include merge tags using the <span className="font-mono">{'{{ variable_name }}'}</span> syntax.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="body_text">Plain Text Body</Label>
              <Textarea
                id="body_text"
                rows={6}
                value={formState.body_text}
                onChange={(event) => handleChange('body_text', event.target.value)}
                placeholder="Hello {{ first_name }}, welcome aboard!"
              />
            </div>

            <div className="flex items-center justify-end gap-3">
              <Button type="button" variant="outline" asChild>
                <Link href="/dashboard/admin/templates">Cancel</Link>
              </Button>
              <Button type="submit" disabled={!isFormValid || isSubmitting}>
                {isSubmitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Changes
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
