'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import type { AxiosError } from 'axios';
import api from '@/config/axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { ArrowLeft, Play, Copy, Eye, Send, AlertCircle, CheckCircle2, Clock, PauseCircle, XCircle, Rocket, Calendar, RotateCcw } from 'lucide-react';
import { useRealtimeUpdates } from '@/hooks/useRealtimeUpdates';
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
    stats_sent?: number;
    stats_delivered?: number;
    stats_opened?: number;
    stats_clicked?: number;
    stats_bounced?: number;
    scheduled_at: string | null;
    created_at: string;
    updated_at: string;
    email_template: unknown;
    email_template_name: string;
    email_provider: unknown;
    email_provider_name: string;
    settings: Record<string, unknown>;
}

interface CampaignAnalytics {
    totals: {
        sent: number;
        delivered: number;
        opened: number;
        clicked: number;
        bounced: number;
        complained: number;
        open_rate: number;
        click_rate: number;
        bounce_rate: number;
        delivery_rate: number;
    };
    engagement?: {
        unique_opens: number;
        total_opens: number;
        unique_clicks: number;
        total_clicks: number;
        hard_bounces: number;
        soft_bounces: number;
        complaints: number;
    };
}

export default function CampaignDetailPage() {
    const { id } = useParams<{ id: string }>();
    const router = useRouter();
    const [campaign, setCampaign] = useState<Campaign | null>(null);
    const [analytics, setAnalytics] = useState<CampaignAnalytics | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [previewContent, setPreviewContent] = useState<string | null>(null);
    const [isPreviewLoading, setIsPreviewLoading] = useState(false);
    const [launchDialogOpen, setLaunchDialogOpen] = useState(false);
    const [duplicateDialogOpen, setDuplicateDialogOpen] = useState(false);
    const [scheduleDialogOpen, setScheduleDialogOpen] = useState(false);
    const [duplicateName, setDuplicateName] = useState('');
    const [scheduledDateTime, setScheduledDateTime] = useState('');
    const [isScheduling, setIsScheduling] = useState(false);
    const [resetDialogOpen, setResetDialogOpen] = useState(false);
    const [isResetting, setIsResetting] = useState(false);
    
    // Real-time updates
    const { onCampaignStatusUpdate } = useRealtimeUpdates();

    const fetchCampaign = useCallback(async () => {
        setIsLoading(true);
        try {
            const response = await api.get(`/campaigns/${id}/`);
            setCampaign(response.data);
            try {
                const analyticsRes = await api.get(`/campaigns/${id}/analytics/`);
                setAnalytics(analyticsRes.data);
            } catch {
                // Analytics may be empty for drafts
                setAnalytics(null);
            }
        } catch (error) {
            console.error(error);
            toast.error('Failed to fetch campaign details');
        } finally {
            setIsLoading(false);
        }
    }, [id]);

    useEffect(() => {
        if (id) {
            fetchCampaign();
        }
    }, [id, fetchCampaign]);

    // Subscribe to real-time campaign status updates
    useEffect(() => {
        if (!id) return;
        
        const unsubscribe = onCampaignStatusUpdate(id, (update) => {
            setCampaign(prev => {
                if (!prev) return null;
                
                const hasStatusChange = prev.status !== update.status;
                
                if (hasStatusChange) {
                    toast.info(`Campaign status changed: ${prev.status} → ${update.status}`, {
                        duration: 3001
                    });
                }
                
                return {
                    ...prev,
                    status: update.status,
                    stats_sent: update.stats_sent,
                    stats_delivered: update.stats_delivered,
                    stats_opened: update.stats_opened,
                    stats_clicked: update.stats_clicked,
                    stats_total_recipients: update.stats_total_recipients,
                    updated_at: update.updated_at
                };
            });
        });
        
        return unsubscribe;
    }, [id, onCampaignStatusUpdate]);

    const handlePreview = async () => {
        setIsPreviewLoading(true);
        try {
            const response = await api.post(`/campaigns/${id}/preview/`);
            setPreviewContent(response.data.html_content || response.data.preview_url);
            toast.success('Preview generated');
        } catch (error: unknown) {
            console.error(error);
            const axiosError = error as AxiosError<{ error?: string }>;
            toast.error(axiosError.response?.data?.error || 'Failed to generate preview');
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
        } catch (error: unknown) {
            console.error(error);
            const axiosError = error as AxiosError<{ error?: string }>;
            toast.error(axiosError.response?.data?.error || 'Failed to launch campaign');
        }
    };

    const handleDuplicateClick = () => {
        setDuplicateName(`${campaign?.name} (Copy)`);
        setDuplicateDialogOpen(true);
    };

    const handleScheduleClick = () => {
        // Set default to tomorrow at 9 AM local time
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        tomorrow.setHours(9, 0, 0, 0);
        
        // Get local ISO string for datetime-local input (YYYY-MM-DDTHH:mm)
        const tzOffset = tomorrow.getTimezoneOffset() * 60000;
        const localISOTime = new Date(tomorrow.getTime() - tzOffset).toISOString().slice(0, 16);
        
        setScheduledDateTime(localISOTime);
        setScheduleDialogOpen(true);
    };

    const handleScheduleConfirm = async () => {
        if (!scheduledDateTime) {
            toast.error('Please select a date and time');
            return;
        }

        const scheduledDate = new Date(scheduledDateTime);
        if (scheduledDate <= new Date()) {
            toast.error('Scheduled time must be in the future');
            return;
        }

        setIsScheduling(true);
        try {
            await api.post(`/campaigns/${id}/schedule/`, {
                scheduled_at: scheduledDateTime
            });
            toast.success('Campaign scheduled successfully!');
            setScheduleDialogOpen(false);
            fetchCampaign();
        } catch (error: unknown) {
            console.error(error);
            const axiosError = error as AxiosError<{ error?: string }>;
            toast.error(axiosError.response?.data?.error || 'Failed to schedule campaign');
        } finally {
            setIsScheduling(false);
        }
    };

    const handleDuplicateConfirm = async () => {
        if (!duplicateName.trim()) return;
        setDuplicateDialogOpen(false);

        try {
            const response = await api.post(`/campaigns/${id}/duplicate/`, { new_name: duplicateName });
            toast.success('Campaign duplicated!');
            router.push(`/dashboard/campaigns/${response.data.id}`);
        } catch (error: unknown) {
            console.error(error);
            const axiosError = error as AxiosError<{ error?: string }>;
            toast.error(axiosError.response?.data?.error || 'Failed to duplicate campaign');
        }
    };

    const handleResetClick = () => {
        setResetDialogOpen(true);
    };

    const handleResetConfirm = async () => {
        setIsResetting(true);
        try {
            const response = await api.post(`/campaigns/${id}/reset/`);
            toast.success(response.data.message || 'Campaign reset to DRAFT');
            setResetDialogOpen(false);
            fetchCampaign();
        } catch (error: unknown) {
            console.error(error);
            const axiosError = error as AxiosError<{ error?: string }>;
            toast.error(axiosError.response?.data?.error || 'Failed to reset campaign');
        } finally {
            setIsResetting(false);
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
                        <>
                            <Button variant="outline" onClick={handleScheduleClick}>
                                <Calendar className="mr-2 h-4 w-4" /> Schedule
                            </Button>
                            <Button onClick={handleLaunchClick} className="bg-gradient-to-r from-primary to-blue-600 hover:opacity-90">
                                <Play className="mr-2 h-4 w-4" /> Launch Campaign
                            </Button>
                        </>
                    )}
                    {campaign.status === 'SCHEDULED' && (
                        <div className="flex items-center gap-2 px-3 py-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                            <Clock className="h-4 w-4 text-orange-600" />
                            <span className="text-sm font-medium text-orange-700 dark:text-orange-400">
                                Scheduled: {campaign.scheduled_at ? new Date(campaign.scheduled_at).toLocaleString() : 'N/A'}
                            </span>
                        </div>
                    )}
                    {['SCHEDULED', 'SENDING', 'PAUSED', 'CANCELLED'].includes(campaign.status) && (
                        <Button variant="outline" onClick={handleResetClick} className="border-amber-500 text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-950">
                            <RotateCcw className="mr-2 h-4 w-4" /> Reset to Draft
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
                                            <p>Click &quot;Preview Content&quot; to see the generated email.</p>
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
                                <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Sent</span>
                                    <span className="font-bold">{analytics?.totals?.sent ?? campaign.stats_sent ?? 0}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Open rate</span>
                                    <span className="font-bold text-blue-600">{analytics?.totals?.open_rate ?? 0}%</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Click rate</span>
                                    <span className="font-bold text-purple-600">{analytics?.totals?.click_rate ?? 0}%</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Bounce rate</span>
                                    <span className="font-bold text-orange-600">{analytics?.totals?.bounce_rate ?? 0}%</span>
                                </div>
                                {analytics?.engagement && (
                                    <>
                                        <div className="border-t pt-2 mt-2" />
                                        <div className="flex justify-between text-sm">
                                            <span className="text-muted-foreground">Total opens</span>
                                            <span className="font-bold">{analytics.engagement.total_opens}</span>
                                        </div>
                                        <div className="flex justify-between text-sm">
                                            <span className="text-muted-foreground">Total clicks</span>
                                            <span className="font-bold">{analytics.engagement.total_clicks}</span>
                                        </div>
                                        <div className="flex justify-between text-sm">
                                            <span className="text-muted-foreground">Hard / soft bounces</span>
                                            <span className="font-bold">
                                                {analytics.engagement.hard_bounces} / {analytics.engagement.soft_bounces}
                                            </span>
                                        </div>
                                    </>
                                )}
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

            {/* Schedule Dialog */}
            <Dialog open={scheduleDialogOpen} onOpenChange={setScheduleDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <div className="flex items-center gap-3">
                            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-orange-100 dark:bg-orange-900/30">
                                <Calendar className="h-6 w-6 text-orange-600" />
                            </div>
                            <div>
                                <DialogTitle>Schedule Campaign</DialogTitle>
                                <DialogDescription>
                                    Choose when you want this campaign to be sent.
                                </DialogDescription>
                            </div>
                        </div>
                    </DialogHeader>
                    <div className="py-4 space-y-4">
                        <div>
                            <Label htmlFor="scheduledAt" className="text-sm font-medium">
                                Send Date & Time
                            </Label>
                            <Input
                                id="scheduledAt"
                                type="datetime-local"
                                value={scheduledDateTime}
                                onChange={(e) => setScheduledDateTime(e.target.value)}
                                min={new Date(new Date().getTime() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 16)}
                                className="mt-2"
                            />
                            <p className="text-xs text-muted-foreground mt-2">
                                Select a future date and time for the campaign to be sent.
                            </p>
                        </div>
                        {scheduledDateTime && (
                            <div className="p-3 rounded-lg bg-muted/50 border">
                                <p className="text-sm">
                                    <span className="text-muted-foreground">Campaign will be sent on:</span>
                                    <br />
                                    <span className="font-semibold">
                                        {new Date(scheduledDateTime).toLocaleString(undefined, {
                                            weekday: 'long',
                                            year: 'numeric',
                                            month: 'long',
                                            day: 'numeric',
                                            hour: '2-digit',
                                            minute: '2-digit'
                                        })}
                                    </span>
                                </p>
                            </div>
                        )}
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setScheduleDialogOpen(false)}>
                            Cancel
                        </Button>
                        <Button 
                            onClick={handleScheduleConfirm}
                            disabled={!scheduledDateTime || isScheduling}
                            className="bg-gradient-to-r from-orange-500 to-orange-600 hover:opacity-90"
                        >
                            {isScheduling ? 'Scheduling...' : 'Schedule Campaign'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Reset Campaign Dialog */}
            <AlertDialog open={resetDialogOpen} onOpenChange={setResetDialogOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <div className="flex items-center gap-3">
                            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/30">
                                <RotateCcw className="h-6 w-6 text-amber-600" />
                            </div>
                            <div>
                                <AlertDialogTitle>Reset Campaign to Draft</AlertDialogTitle>
                                <AlertDialogDescription>
                                    This will reset the campaign status back to DRAFT. Any scheduled time will be cleared. 
                                    Use this if the campaign is stuck or you want to make changes.
                                </AlertDialogDescription>
                            </div>
                        </div>
                    </AlertDialogHeader>
                    <div className="my-4 p-3 rounded-lg bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-800">
                        <p className="text-sm text-amber-800 dark:text-amber-200">
                            <strong>Current Status:</strong> {campaign?.status}
                        </p>
                        <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
                            After reset, you can edit and re-launch or re-schedule the campaign.
                        </p>
                    </div>
                    <AlertDialogFooter>
                        <AlertDialogCancel disabled={isResetting}>Cancel</AlertDialogCancel>
                        <AlertDialogAction 
                            onClick={handleResetConfirm}
                            disabled={isResetting}
                            className="bg-amber-600 hover:bg-amber-700"
                        >
                            {isResetting ? 'Resetting...' : 'Reset to Draft'}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
