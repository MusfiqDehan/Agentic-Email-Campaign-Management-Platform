'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Checkbox } from '@/components/ui/checkbox';
import { toast } from 'sonner';
import { ArrowLeft, ArrowRight, Check, Send } from 'lucide-react';
import Link from 'next/link';
import Editor from '@/components/editor';

export default function NewCampaignPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  
  // Form State
  const [name, setName] = useState('');
  const [subject, setSubject] = useState('');
  const [content, setContent] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [selectedLists, setSelectedLists] = useState<string[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  
  // Data State
  const [templates, setTemplates] = useState<any[]>([]);
  const [contactLists, setContactLists] = useState<any[]>([]);
  const [providers, setProviders] = useState<any[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [templatesRes, listsRes, providersRes] = await Promise.all([
          api.get('/campaigns/email-templates/'),
          api.get('/campaigns/contact-lists/'),
          api.get('/campaigns/organization-providers/')
        ]);
        setTemplates(templatesRes.data);
        setContactLists(listsRes.data);
        setProviders(providersRes.data);
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
      setContent(template.html_content);
      if (!subject) setSubject(template.subject || '');
    }
  };

  const handleListToggle = (listId: string) => {
    setSelectedLists(prev => 
      prev.includes(listId) 
        ? prev.filter(id => id !== listId)
        : [...prev, listId]
    );
  };

  const handleLaunch = async (status: 'SCHEDULED' | 'SENDING') => {
    if (!name || !subject || !content || selectedLists.length === 0 || !selectedProvider) {
      toast.error('Please complete all steps');
      return;
    }

    setIsLoading(true);
    try {
      // 1. Create Campaign
      const campaignRes = await api.post('/campaigns/campaigns/', {
        name,
        subject,
        html_content: content,
        contact_lists: selectedLists,
        status: 'DRAFT' // Create as draft first
      });
      
      const campaignId = campaignRes.data.id;

      // 2. Launch or Schedule (For now just launch immediately if SENDING)
      if (status === 'SENDING') {
        await api.post(`/campaigns/campaigns/${campaignId}/launch/`);
        toast.success('Campaign launched successfully!');
      } else {
        // Just leave as draft or scheduled
        toast.success('Campaign saved as draft');
      }
      
      router.push('/dashboard/campaigns');
    } catch (error: any) {
      console.error(error);
      toast.error(error.response?.data?.detail || 'Failed to launch campaign');
    } finally {
      setIsLoading(false);
    }
  };

  const nextStep = () => setStep(s => Math.min(s + 1, 5));
  const prevStep = () => setStep(s => Math.max(s - 1, 1));

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
      <div className="flex justify-between items-center px-10 py-4 bg-white rounded-lg border">
        {[1, 2, 3, 4, 5].map((s) => (
          <div key={s} className="flex flex-col items-center gap-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
              step >= s ? 'bg-primary text-primary-foreground' : 'bg-gray-100 text-gray-500'
            }`}>
              {step > s ? <Check className="h-4 w-4" /> : s}
            </div>
            <span className="text-xs text-muted-foreground">
              {s === 1 ? 'Details' : s === 2 ? 'Content' : s === 3 ? 'Audience' : s === 4 ? 'Config' : 'Review'}
            </span>
          </div>
        ))}
      </div>

      <Card className="min-h-[400px]">
        <CardContent className="pt-6">
          {step === 1 && (
            <div className="space-y-4 max-w-md mx-auto">
              <div className="space-y-2">
                <Label htmlFor="name">Campaign Name</Label>
                <Input 
                  id="name" 
                  placeholder="e.g., Summer Sale 2025" 
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="subject">Email Subject</Label>
                <Input 
                  id="subject" 
                  placeholder="e.g., Don't miss out on these deals!" 
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                />
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6">
              <div className="flex gap-4 items-center">
                <Label>Load Template:</Label>
                <Select value={selectedTemplate} onValueChange={handleTemplateSelect}>
                  <SelectTrigger className="w-[250px]">
                    <SelectValue placeholder="Select a template" />
                  </SelectTrigger>
                  <SelectContent>
                    {templates.map(t => (
                      <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Email Content</Label>
                <Editor 
                  value={content} 
                  onChange={setContent} 
                  placeholder="Design your email..."
                />
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Select Contact Lists</h3>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {contactLists.map(list => (
                  <div 
                    key={list.id} 
                    className={`p-4 rounded-lg border cursor-pointer transition-all ${
                      selectedLists.includes(list.id) ? 'border-primary bg-primary/5 ring-1 ring-primary' : 'hover:border-gray-400'
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
                {contactLists.length === 0 && (
                  <div className="col-span-full text-center py-10 text-muted-foreground">
                    No contact lists found. <Link href="/dashboard/contacts" className="text-primary underline">Create one first.</Link>
                  </div>
                )}
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-4 max-w-md mx-auto">
              <div className="space-y-2">
                <Label>Select Sending Provider</Label>
                <Select value={selectedProvider} onValueChange={setSelectedProvider}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a provider" />
                  </SelectTrigger>
                  <SelectContent>
                    {providers.map(p => (
                      <SelectItem key={p.id} value={p.id}>
                        {p.name} ({p.provider_type})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {providers.length === 0 && (
                  <p className="text-sm text-red-500">
                    No providers found. <Link href="/dashboard/settings/providers/new" className="underline">Add one first.</Link>
                  </p>
                )}
              </div>
            </div>
          )}

          {step === 5 && (
            <div className="space-y-6 max-w-2xl mx-auto">
              <h3 className="text-xl font-bold">Review Campaign</h3>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-1">
                  <span className="text-sm text-muted-foreground">Name</span>
                  <p className="font-medium">{name}</p>
                </div>
                <div className="space-y-1">
                  <span className="text-sm text-muted-foreground">Subject</span>
                  <p className="font-medium">{subject}</p>
                </div>
                <div className="space-y-1">
                  <span className="text-sm text-muted-foreground">Audience</span>
                  <p className="font-medium">{selectedLists.length} lists selected</p>
                </div>
                <div className="space-y-1">
                  <span className="text-sm text-muted-foreground">Provider</span>
                  <p className="font-medium">
                    {providers.find(p => p.id === selectedProvider)?.name || 'Unknown'}
                  </p>
                </div>
              </div>
              <div className="rounded-md border p-4 bg-gray-50 max-h-60 overflow-auto">
                <span className="text-xs text-muted-foreground block mb-2">Content Preview (HTML)</span>
                <div dangerouslySetInnerHTML={{ __html: content }} className="prose prose-sm max-w-none" />
              </div>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex justify-between border-t p-6">
          <Button variant="outline" onClick={prevStep} disabled={step === 1}>
            Back
          </Button>
          
          {step < 5 ? (
            <Button onClick={nextStep}>
              Next <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          ) : (
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => handleLaunch('SCHEDULED')} disabled={isLoading}>
                Save Draft
              </Button>
              <Button onClick={() => handleLaunch('SENDING')} disabled={isLoading}>
                <Send className="mr-2 h-4 w-4" /> Launch Now
              </Button>
            </div>
          )}
        </CardFooter>
      </Card>
    </div>
  );
}
