'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/config/axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { toast } from 'sonner';
import type { AxiosError } from 'axios';
import { ArrowLeft, ArrowRight, Check } from 'lucide-react';
import Link from 'next/link';

interface Template {
  id: string;
  template_name: string;
  email_subject?: string;
  preview_text?: string;
  email_body: string;
}

interface ContactList {
  id: string;
  name: string;
  total_contacts: number;
}

interface Provider {
  id: string;
  name: string;
  provider_type?: string;
}

export default function NewCampaignPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);

  // Form State
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [subject, setSubject] = useState('');
  const [previewText, setPreviewText] = useState('');
  const [tags, setTags] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [selectedLists, setSelectedLists] = useState<string[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');

  // Settings
  const [trackOpens, setTrackOpens] = useState(true);
  const [trackClicks, setTrackClicks] = useState(true);
  const [includeUnsubscribe, setIncludeUnsubscribe] = useState(true);

  // Variables
  const [variables, setVariables] = useState<Record<string, string>>({
    company_name: '',
    first_name: '',
    year: new Date().getFullYear().toString(),
  });

  // Data State
  const [templates, setTemplates] = useState<Template[]>([]);
  const [contactLists, setContactLists] = useState<ContactList[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [templatesRes, listsRes, providersRes] = await Promise.all([
          api.get('/campaigns/templates/'),
          api.get('/campaigns/contact-lists/'),
          api.get('/campaigns/org/providers/')
        ]);

        const templatesData = Array.isArray(templatesRes.data) ? templatesRes.data : (templatesRes.data.data || []);
        const listsData = Array.isArray(listsRes.data) ? listsRes.data : (listsRes.data.data || []);
        const providersData = Array.isArray(providersRes.data) ? providersRes.data : (providersRes.data.data || []);

        setTemplates(templatesData);
        setContactLists(listsData);
        setProviders(providersData);
      } catch (error) {
        console.error(error);
        toast.error('Failed to load campaign resources');
      }
    };
    fetchData();
  }, []);

  const handleTemplateSelect = (templateId: string) => {
    setSelectedTemplate(templateId);
    const template = templates.find(t => t.id === templateId);
    if (template) {
      if (!subject) setSubject(template.email_subject || '');
      if (!previewText) setPreviewText(template.preview_text || '');
    }
  };

  const handleVariableChange = (key: string, value: string) => {
    setVariables(prev => ({ ...prev, [key]: value }));
  };

  const handleListToggle = (listId: string) => {
    setSelectedLists(prev =>
      prev.includes(listId)
        ? prev.filter(id => id !== listId)
        : [...prev, listId]
    );
  };

  const buildPayload = () => {
    return {
      name,
      description,
      subject,
      preview_text: previewText,
      email_template: selectedTemplate,
      contact_lists: selectedLists,
      email_provider: selectedProvider,
      tags: tags.split(',').map(tag => tag.trim()).filter(tag => tag !== ''),
      settings: {
        track_opens: trackOpens,
        track_clicks: trackClicks,
        include_unsubscribe: includeUnsubscribe
      },
      email_variables: variables
    };
  };

  const handleCreate = async () => {
    if (!name || !subject || !selectedTemplate || selectedLists.length === 0 || !selectedProvider) {
      toast.error('Please complete all required fields');
      return;
    }

    setIsLoading(true);
    try {
      const payload = buildPayload();
      await api.post('/campaigns/', payload);
      toast.success('Campaign created successfully!');
      router.push('/dashboard/campaigns');
    } catch (error: unknown) {
      console.error(error);
      const axiosError = error as AxiosError<{ detail?: string; error?: string }>;
      toast.error(axiosError.response?.data?.detail || axiosError.response?.data?.error || 'Failed to create campaign');
    } finally {
      setIsLoading(false);
    }
  };

  const nextStep = () => setStep(s => Math.min(s + 1, 6));
  const prevStep = () => setStep(s => Math.max(s - 1, 1));

  const currentTemplate = templates.find(t => t.id === selectedTemplate);

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-20">
      <div className="flex items-center gap-4">
        <Link href="/dashboard/campaigns">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h2 className="text-3xl font-bold tracking-tight">New Campaign</h2>
          <p className="text-muted-foreground">Create and launch a new email campaign.</p>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="flex justify-between items-center px-10 py-4 bg-card rounded-xl border shadow-sm">
        {[1, 2, 3, 4, 5, 6].map((s) => (
          <div key={s} className="flex flex-col items-center gap-2">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-all duration-300 ${step >= s ? 'bg-gradient-to-br from-primary to-blue-600 text-white shadow-lg shadow-primary/30' : 'bg-muted text-muted-foreground'
              }`}>
              {step > s ? <Check className="h-4 w-4" /> : s}
            </div>
            <span className="text-xs text-muted-foreground text-center">
              {s === 1 ? 'Details' : s === 2 ? 'Content' : s === 3 ? 'Audience' : s === 4 ? 'Settings' : s === 5 ? 'Variables' : 'Review'}
            </span>
          </div>
        ))}
      </div>

      <Card className="min-h-[450px]">
        <CardContent className="pt-6">
          {step === 1 && (
            <div className="space-y-4 max-w-xl mx-auto">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="name">Campaign Name*</Label>
                  <Input
                    id="name"
                    placeholder="e.g., January Newsletter"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="tags">Tags (comma separated)</Label>
                  <Input
                    id="tags"
                    placeholder="newsletter, marketing"
                    value={tags}
                    onChange={(e) => setTags(e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description (Internal)</Label>
                <Input
                  id="description"
                  placeholder="What is this campaign about?"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="subject">Email Subject*</Label>
                <Input
                  id="subject"
                  placeholder="The subject line recipients will see"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="preview_text">Preview Text</Label>
                <Input
                  id="preview_text"
                  placeholder="Short summary shown in inbox"
                  value={previewText}
                  onChange={(e) => setPreviewText(e.target.value)}
                />
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6">
              <div className="flex gap-4 items-center max-w-md mx-auto">
                <Label className="whitespace-nowrap">Select Template*</Label>
                <Select value={selectedTemplate} onValueChange={handleTemplateSelect}>
                  <SelectTrigger>
                    <SelectValue placeholder="Chose an email template" />
                  </SelectTrigger>
                  <SelectContent>
                    {templates.map(t => (
                      <SelectItem key={t.id} value={t.id}>{t.template_name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {currentTemplate && (
                <div className="max-w-3xl mx-auto rounded-xl border p-6 bg-muted/50">
                  <h4 className="text-sm font-medium mb-4 text-muted-foreground uppercase tracking-wider">Template Preview</h4>
                  <div
                    dangerouslySetInnerHTML={{ __html: currentTemplate.email_body }}
                    className="prose prose-sm max-w-none bg-card p-6 rounded-lg border shadow-sm max-h-[400px] overflow-auto dark:prose-invert"
                  />
                </div>
              )}
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-center">Target Audience</h3>
              <p className="text-sm text-muted-foreground text-center mb-6">Select which contact lists should receive this campaign.</p>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {contactLists.map(list => (
                  <div
                    key={list.id}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${selectedLists.includes(list.id) ? 'border-primary bg-primary/10 ring-2 ring-primary shadow-lg shadow-primary/10' : 'hover:border-primary/50 hover:bg-muted/50'
                      }`}
                    onClick={() => handleListToggle(list.id)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium">{list.name}</h4>
                      {selectedLists.includes(list.id) && <Check className="h-4 w-4 text-primary" />}
                    </div>
                    <p className="text-sm text-muted-foreground">{list.total_contacts} contacts</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-8 max-w-md mx-auto">
              <div className="space-y-4">
                <Label className="text-lg font-medium block text-center">Sending Configuration</Label>
                <div className="space-y-2">
                  <Label>Email Provider*</Label>
                  <Select value={selectedProvider} onValueChange={setSelectedProvider}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a sending service" />
                    </SelectTrigger>
                    <SelectContent>
                      {providers.map(p => (
                        <SelectItem key={p.id} value={p.id}>
                          {p.name} ({p.provider_type})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-4 pt-4 border-t">
                <Label className="text-lg font-medium block text-center">Tracking & Settings</Label>
                <div className="space-y-4 bg-muted/50 p-4 rounded-xl border">
                  <div className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/80 transition-colors">
                    <Label htmlFor="track-opens" className="flex-1 cursor-pointer">Track Email Opens</Label>
                    <Checkbox id="track-opens" checked={trackOpens} onCheckedChange={(val) => setTrackOpens(val as boolean)} />
                  </div>
                  <div className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/80 transition-colors">
                    <Label htmlFor="track-clicks" className="flex-1 cursor-pointer">Track Link Clicks</Label>
                    <Checkbox id="track-clicks" checked={trackClicks} onCheckedChange={(val) => setTrackClicks(val as boolean)} />
                  </div>
                  <div className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/80 transition-colors">
                    <Label htmlFor="include-unsub" className="flex-1 cursor-pointer">Include Unsubscribe Link</Label>
                    <Checkbox id="include-unsub" checked={includeUnsubscribe} onCheckedChange={(val) => setIncludeUnsubscribe(val as boolean)} />
                  </div>
                </div>
              </div>
            </div>
          )}

          {step === 5 && (
            <div className="space-y-6 max-w-md mx-auto text-center">
              <h3 className="text-lg font-medium">Email Variables</h3>
              <p className="text-sm text-muted-foreground mb-6">Provide values for placeholders in your template.</p>

              <div className="space-y-4 text-left">
                <div className="space-y-2">
                  <Label>Company Name</Label>
                  <Input
                    value={variables.company_name}
                    onChange={(e) => handleVariableChange('company_name', e.target.value)}
                    placeholder="e.g., Acme Corp"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Recipient First Name Placeholder</Label>
                  <Input
                    value={variables.first_name}
                    onChange={(e) => handleVariableChange('first_name', e.target.value)}
                    placeholder="Default if first name is missing"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Current Year</Label>
                  <Input
                    value={variables.year}
                    onChange={(e) => handleVariableChange('year', e.target.value)}
                  />
                </div>
              </div>
            </div>
          )}

          {step === 6 && (
            <div className="space-y-6 max-w-3xl mx-auto">
              <h3 className="text-xl font-bold text-center">Review & Send</h3>
              <div className="grid gap-6 md:grid-cols-2 p-6 rounded-xl bg-muted/50 border">
                <div className="space-y-4">
                  <div className="space-y-1">
                    <span className="text-xs text-muted-foreground uppercase">Campaign Name</span>
                    <p className="font-semibold">{name}</p>
                  </div>
                  <div className="space-y-1">
                    <span className="text-xs text-muted-foreground uppercase">Subject Line</span>
                    <p className="font-semibold">{subject}</p>
                  </div>
                  <div className="space-y-1">
                    <span className="text-xs text-muted-foreground uppercase">Provider</span>
                    <p className="font-semibold">
                      {providers.find(p => p.id === selectedProvider)?.name || 'Not selected'}
                    </p>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="space-y-1">
                    <span className="text-xs text-muted-foreground uppercase">Audience</span>
                    <p className="font-semibold">{selectedLists.length} lists selected</p>
                  </div>
                  <div className="space-y-1">
                    <span className="text-xs text-muted-foreground uppercase">Template</span>
                    <p className="font-semibold">{currentTemplate?.template_name || 'Not selected'}</p>
                  </div>
                  <div className="space-y-1">
                    <span className="text-xs text-muted-foreground uppercase">Tracking</span>
                    <p className="text-sm">
                      Opens: {trackOpens ? 'Yes' : 'No'} • Clicks: {trackClicks ? 'Yes' : 'No'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex justify-between border-t p-6">
          <Button variant="outline" onClick={prevStep} disabled={step === 1 || isLoading}>
            Back
          </Button>

          {step < 6 ? (
            <Button onClick={nextStep} disabled={isLoading} className="bg-gradient-to-r from-primary to-blue-600 hover:opacity-90">
              Next <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          ) : (
            <Button onClick={handleCreate} disabled={isLoading} className="px-8 bg-gradient-to-r from-primary to-blue-600 hover:opacity-90">
              {isLoading ? 'Creating...' : 'Create Campaign'}
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  );
}
