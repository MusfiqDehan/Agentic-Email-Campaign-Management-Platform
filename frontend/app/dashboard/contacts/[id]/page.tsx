'use client';

import { useCallback, useEffect, useState, use } from 'react';
import Link from 'next/link';
import api from '@/config/axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ArrowLeft, Mail, Calendar, CheckCircle, XCircle, Copy, Check, Link as LinkIcon } from 'lucide-react';
import { toast } from 'sonner';

interface Contact {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    is_active: boolean;
    status: string;
    created_at: string;
}

interface ContactList {
    id: string;
    name: string;
    description?: string;
    subscription_token?: string;
    double_opt_in?: boolean;
    total_contacts?: number;
    active_contacts?: number;
}

export default function ContactListDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const [contacts, setContacts] = useState<Contact[]>([]);
    const [listInfo, setListInfo] = useState<ContactList | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [copied, setCopied] = useState(false);

    const copyToClipboard = async (text: string) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            toast.success('Subscription token copied to clipboard!');
            setTimeout(() => setCopied(false), 2000);
        } catch {
            toast.error('Failed to copy to clipboard');
        }
    };

    const fetchData = useCallback(async () => {
        setIsLoading(true);
        try {
            // Fetch list details
            const listResponse = await api.get(`/campaigns/contact-lists/${id}/`);
            const listData = listResponse.data.data || listResponse.data;
            setListInfo(listData);

            // Fetch contacts for this list
            const contactsResponse = await api.get(`/campaigns/contacts/?list=${id}`);
            // Handle both raw array and wrapped data object
            const contactsData = Array.isArray(contactsResponse.data) ? contactsResponse.data : (contactsResponse.data.data || []);
            setContacts(contactsData);
        } catch (error) {
            console.error(error);
            toast.error('Failed to fetch contact details');
        } finally {
            setIsLoading(false);
        }
    }, [id]);

    useEffect(() => {
        fetchData();

        const handleRefresh = () => fetchData();
        window.addEventListener('agent-action-completed', handleRefresh);
        return () => window.removeEventListener('agent-action-completed', handleRefresh);
    }, [fetchData]);

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-4">
                <Link href="/dashboard/contacts">
                    <Button variant="ghost" size="icon">
                        <ArrowLeft className="h-4 w-4" />
                    </Button>
                </Link>
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">
                        {listInfo?.name || 'Contact List'}
                    </h2>
                    <p className="text-muted-foreground">View and manage contacts in this list.</p>
                </div>
            </div>

            {/* Subscription Token Card */}
            {listInfo?.subscription_token && (
                <Card className="border-dashed border-2 border-primary/20 bg-primary/5">
                    <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <LinkIcon className="h-5 w-5 text-primary" />
                                <CardTitle className="text-lg">Public Subscription Token</CardTitle>
                            </div>
                            {listInfo.double_opt_in && (
                                <span className="text-xs bg-amber-100 text-amber-800 px-2 py-1 rounded-full">
                                    Double Opt-In Enabled
                                </span>
                            )}
                        </div>
                        <CardDescription>
                            Use this token in your signup forms to allow public subscriptions to this list.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center gap-2">
                            <code className="flex-1 bg-background border rounded-lg px-4 py-3 font-mono text-sm break-all">
                                {listInfo.subscription_token}
                            </code>
                            <Button
                                variant="outline"
                                size="icon"
                                className="shrink-0 h-12 w-12"
                                onClick={() => copyToClipboard(listInfo.subscription_token!)}
                            >
                                {copied ? (
                                    <Check className="h-4 w-4 text-green-500" />
                                ) : (
                                    <Copy className="h-4 w-4" />
                                )}
                            </Button>
                        </div>
                        <p className="text-xs text-muted-foreground mt-3">
                            API Endpoint: <code className="bg-muted px-1 rounded">POST /api/v1/campaigns/public/subscribe/</code>
                        </p>
                    </CardContent>
                </Card>
            )}

            <Card>
                <CardHeader>
                    <CardTitle className="text-xl font-semibold flex items-center gap-2">
                        Contacts ({contacts.length})
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div className="flex items-center justify-center h-64">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                        </div>
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Email</TableHead>
                                    <TableHead>First Name</TableHead>
                                    <TableHead>Last Name</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Joined</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {contacts.map((contact) => (
                                    <TableRow key={contact.id}>
                                        <TableCell className="font-medium">
                                            <div className="flex items-center gap-2">
                                                <Mail className="h-4 w-4 text-muted-foreground" />
                                                {contact.email}
                                            </div>
                                        </TableCell>
                                        <TableCell>{contact.first_name || '-'}</TableCell>
                                        <TableCell>{contact.last_name || '-'}</TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-1">
                                                {contact.status === 'ACTIVE' || contact.is_active ? (
                                                    <>
                                                        <CheckCircle className="h-4 w-4 text-green-500" />
                                                        <span className="text-green-700 capitalize">{contact.status.toLowerCase()}</span>
                                                    </>
                                                ) : (
                                                    <>
                                                        <XCircle className="h-4 w-4 text-red-500" />
                                                        <span className="text-red-700 capitalize">{contact.status?.toLowerCase() || 'Inactive'}</span>
                                                    </>
                                                )}
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-2 text-muted-foreground">
                                                <Calendar className="h-4 w-4" />
                                                {contact.created_at ? new Date(contact.created_at).toLocaleDateString() : '-'}
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ))}
                                {contacts.length === 0 && (
                                    <TableRow>
                                        <TableCell colSpan={5} className="h-32 text-center text-muted-foreground">
                                            No contacts found in this list.
                                        </TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
