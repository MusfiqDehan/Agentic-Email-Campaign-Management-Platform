'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus, FileText, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

interface Template {
  id: string;
  name: string;
  subject: string;
  created_at: string;
}

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchTemplates = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/campaigns/templates/');
      setTemplates(response.data.data || []);
    } catch (error) {
      console.error(error);
      toast.error('Failed to fetch templates');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this template?')) return;
    try {
      await api.delete(`/campaigns/templates/${id}/`);
      toast.success('Template deleted');
      fetchTemplates();
    } catch (error) {
      console.error(error);
      toast.error('Failed to delete template');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Email Templates</h2>
          <p className="text-muted-foreground">Create and manage your email designs.</p>
        </div>
        <Link href="/dashboard/templates/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" /> Create Template
          </Button>
        </Link>
      </div>

      {isLoading ? (
        <div>Loading...</div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {templates.map((template) => (
            <Card key={template.id} className="hover:bg-gray-50 transition-colors">
              <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                <div className="space-y-1">
                  <CardTitle className="text-base font-medium flex items-center gap-2">
                    <FileText className="h-4 w-4 text-primary" />
                    {template.name}
                  </CardTitle>
                </div>
                <Button variant="ghost" size="icon" className="text-destructive" onClick={() => handleDelete(template.id)}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground truncate">
                  Subject: {template.subject || 'No subject'}
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  Created: {new Date(template.created_at).toLocaleDateString()}
                </p>
              </CardContent>
            </Card>
          ))}
          {templates.length === 0 && (
            <div className="col-span-full flex h-32 items-center justify-center rounded-lg border border-dashed">
              <p className="text-muted-foreground">No templates found.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
