'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { toast } from 'sonner';
import { ArrowLeft, Play, Copy, Eye, Send, AlertCircle, CheckCircle2, Clock, PauseCircle, XCircle, Rocket } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface Campaign {
    id: string;
    name: string;
    description: string;
    subject: string;
    preview_text: string;
    status: string;
    tags: string[];
    total_recipients: number; // For backward compat if needed
    stats_total_recipients: number;
    created_at: string;
    updated_at: string;
    email_template: any;
    email_template_name: string;
    email_provider: any;
    email_provider_name: string;
    settings: any;
}

export default function CampaignDetailPage() {
    const { id } = useParams();
    const router = useRouter();
    const [campaign, setCampaign] = useState<Campaign | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [previewContent, setPreviewContent] = useState<string | null>(null);
    const [isPreviewLoading, setIsPreviewLoading] = useState(false);
    const [launchDialogOpen, setLaunchDialogOpen] = useState(false);
    const [duplicateDialogOpen, setDuplicateDialogOpen] = useState(false);
    const [duplicateName, setDuplicateName] = useState('');

    const fetchCampaign = async () => {
        setIsLoading(true);
        try {
            const response = await api.get(`/campaigns/${id}/`);
            setCampaign(response.data);
        } catch (error) {
            console.error(error);
            toast.error('Failed to fetch campaign details');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (id) {
            fetchCampaign();
        }
    }, [id]);

    const handlePreview = async () => {
        setIsPreviewLoading(true);
        try {
            const response = await api.post(`/campaigns/${id}/preview/`);
            setPreviewContent(response.data.html_content || response.data.preview_url);
            toast.success('Preview generated');
        } catch (error: any) {
            console.error(error);
            toast.error(error.response?.data?.error || 'Failed to generate preview');
        } finally {
            setIsPreviewLoading(false);
        }
    };

    const handleLaunchClick = () => {
        setLaunchDialogOpen(true);
    };

    const handleLaunchConfirm = async () => {
        setLaunchDialogOpen(false);
        try {
            await api.post(`/campaigns/${id}/launch/`);
            toast.success('Campaign launched successfully!');
            fetchCampaign();
        } catch (error: any) {
            console.error(error);
            toast.error(error.response?.data?.error || 'Failed to launch campaign');
        }
    };

    const handleDuplicateClick = () => {
        setDuplicateName(`${campaign?.name} (Copy)`);
        setDuplicateDialogOpen(true);
    };

    const handleDuplicateConfirm = async () => {
        if (!duplicateName.trim()) return;
        setDuplicateDialogOpen(false);

        try {
            const response = await api.post(`/campaigns/${id}/duplicate/`, { new_name: duplicateName });
            toast.success('Campaign duplicated!');
            router.push(`/dashboard/campaigns/${response.data.id}`);
        } catch (error: any) {
            console.error(error);
            toast.error(error.response?.data?.error || 'Failed to duplicate campaign');
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'SENT': return <CheckCircle2 className="h-5 w-5 text-green-500" />;
            case 'SENDING': return <Send className="h-5 w-5 text-blue-500 animate-pulse" />;
            case 'DRAFT': return <Clock className="h-5 w-5 text-gray-500" />;
            case 'SCHEDULED': return <Clock className="h-5 w-5 text-orange-500" />;
            case 'PAUSED': return <PauseCircle className="h-5 w-5 text-yellow-500" />;
            case 'CANCELLED': return <XCircle className="h-5 w-5 text-red-500" />;
            default: return <AlertCircle className="h-5 w-5 text-gray-500" />;
        }
    };

    if (isLoading) return <div className="p-8 text-center text-muted-foreground">Loading campaign details...</div>;
    if (!campaign) return <div className="p-8 text-center text-red-500">Campaign not found</div>;

    return (
        <div className="space-y-6 max-w-6xl mx-auto pb-20">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Link href="/dashboard/campaigns">
                        <Button variant="ghost" size="icon">
                            <ArrowLeft className="h-4 w-4" />
                        </Button>
                    </Link>
                    <div>
                        <div className="flex items-center gap-2">
                            <h2 className="text-3xl font-bold tracking-tight">{campaign.name}</h2>
                            {getStatusIcon(campaign.status)}
                        </div>
                        <p className="text-muted-foreground">{campaign.description || 'No description provided'}</p>
                    </div>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={handleDuplicateClick}>
                        <Copy className="mr-2 h-4 w-4" /> Duplicate
                    </Button>
                    <Button variant="outline" onClick={handlePreview} disabled={isPreviewLoading}>
                        <Eye className="mr-2 h-4 w-4" /> {isPreviewLoading ? 'Generating...' : 'Preview Content'}
                    </Button>
                    {campaign.status === 'DRAFT' && (
                        <Button onClick={handleLaunchClick} className="bg-gradient-to-r from-primary to-blue-600 hover:opacity-90">
                            <Play className="mr-2 h-4 w-4" /> Launch Campaign
                        </Button>
                    )}
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
                <div className="md:col-span-2 space-y-6">
                    <Card>
                        <CardHeader>
                            <CardTitle>Email Content</CardTitle>
                            <CardDescription>Generated subject and preview text</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-1">
                                <span className="text-xs text-muted-foreground uppercase">Subject Line</span>
                                <p className="font-semibold text-lg">{campaign.subject}</p>
                            </div>
                            <div className="space-y-1">
                                <span className="text-xs text-muted-foreground uppercase">Preview Text</span>
                                <p className="text-sm border-l-2 pl-3 italic text-muted-foreground">
                                    {campaign.preview_text || 'No preview text set'}
                                </p>
                            </div>
                        </CardContent>
                    </Card>

                    <Tabs defaultValue="preview">
                        <TabsList className="w-full justify-start">
                            <TabsTrigger value="preview">Live Preview</TabsTrigger>
                            <TabsTrigger value="details">Technical Details</TabsTrigger>
                        </TabsList>
                        <TabsContent value="preview" className="mt-4">
                            <Card>
                                <CardContent className="pt-6">
                                    {previewContent ? (
                                        <div className="rounded-xl border bg-card min-h-[500px] overflow-auto">
                                            <div dangerouslySetInnerHTML={{ __html: previewContent }} className="prose prose-sm max-w-none dark:prose-invert p-6" />
                                        </div>
                                    ) : (
                                        <div className="flex flex-col items-center justify-center min-h-[400px] bg-muted/50 border border-dashed rounded-xl text-muted-foreground">
                                            <Eye className="h-12 w-12 mb-4 opacity-20" />
                                            <p>Click "Preview Content" to see the generated email.</p>
                                            <Button variant="link" onClick={handlePreview} disabled={isPreviewLoading}>
                                                Generate Preview Now
                                            </Button>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </TabsContent>
                        <TabsContent value="details" className="mt-4">
                            <Card>
                                <CardContent className="pt-6">
                                    <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                                        <div>
                                            <dt className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Template</dt>
                                            <dd className="mt-1 text-sm font-semibold">{campaign.email_template_name || 'N/A'}</dd>
                                        </div>
                                        <div>
                                            <dt className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Provider</dt>
                                            <dd className="mt-1 text-sm font-semibold">{campaign.email_provider_name || 'N/A'}</dd>
                                        </div>
                                        <div>
                                            <dt className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Tags</dt>
                                            <dd className="mt-1 flex flex-wrap gap-1">
                                                {campaign.tags && campaign.tags.length > 0 ? (
                                                    campaign.tags.map(tag => <Badge key={tag} variant="secondary">{tag}</Badge>)
                                                ) : 'None'}
                                            </dd>
                                        </div>
                                        <div>
                                            <dt className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Created</dt>
                                            <dd className="mt-1 text-sm">{new Date(campaign.created_at).toLocaleString()}</dd>
                                        </div>
                                    </dl>
                                </CardContent>
                            </Card>
                        </TabsContent>
                    </Tabs>
                </div>

                <div className="space-y-6">
                    <Card>
                        <CardHeader>
                            <CardTitle>Campaign Status</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="flex items-center justify-between p-3 rounded-xl bg-muted/50 border">
                                <span className="text-sm font-medium">Current Status</span>
                                <Badge variant={campaign.status === 'SENT' ? 'default' : 'outline'}>{campaign.status}</Badge>
                            </div>

                            <div className="space-y-2">
                                <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Recipients</span>
                                    <span className="font-bold">{campaign.stats_total_recipients || 0}</span>
                                </div>
                                {/* Add more stats here if available from API */}
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>Settings</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2">
                            {campaign.settings && Object.entries(campaign.settings).map(([key, value]) => (
                                <div key={key} className="flex justify-between items-center text-sm py-1">
                                    <span className="text-muted-foreground capitalize">{key.replace(/_/g, ' ')}</span>
                                    <Badge variant={value ? "outline" : "secondary"}>{String(value)}</Badge>
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* Launch Confirmation Dialog */}
            <AlertDialog open={launchDialogOpen} onOpenChange={setLaunchDialogOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <div className="flex items-center gap-3">
                            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                                <Rocket className="h-6 w-6 text-primary" />
                            </div>
                            <div>
                                <AlertDialogTitle>Launch Campaign</AlertDialogTitle>
                                <AlertDialogDescription>
                                    Are you sure you want to launch this campaign? This will start sending emails to your contact lists.
                                </AlertDialogDescription>
                            </div>
                        </div>
                    </AlertDialogHeader>
                    <AlertDialogFooter className="mt-4">
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction 
                            onClick={handleLaunchConfirm}
                            className="bg-gradient-to-r from-primary to-blue-600 hover:opacity-90"
                        >
                            Launch Now
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            {/* Duplicate Dialog */}
            <Dialog open={duplicateDialogOpen} onOpenChange={setDuplicateDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <div className="flex items-center gap-3">
                            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                                <Copy className="h-6 w-6 text-primary" />
                            </div>
                            <div>
                                <DialogTitle>Duplicate Campaign</DialogTitle>
                                <DialogDescription>
                                    Create a copy of this campaign with a new name.
                                </DialogDescription>
                            </div>
                        </div>
                    </DialogHeader>
                    <div className="py-4">
                        <Label htmlFor="duplicateName" className="text-sm font-medium">
                            Campaign Name
                        </Label>
                        <Input
                            id="duplicateName"
                            value={duplicateName}
                            onChange={(e) => setDuplicateName(e.target.value)}
                            placeholder="Enter campaign name"
                            className="mt-2"
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') handleDuplicateConfirm();
                            }}
                        />
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setDuplicateDialogOpen(false)}>
                            Cancel
                        </Button>
                        <Button 
                            onClick={handleDuplicateConfirm}
                            disabled={!duplicateName.trim()}
                            className="bg-gradient-to-r from-primary to-blue-600 hover:opacity-90"
                        >
                            Duplicate
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
