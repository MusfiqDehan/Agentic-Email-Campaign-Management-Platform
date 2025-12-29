'use client';

import { useEffect, useState, use } from 'react';
import Link from 'next/link';
import api from '@/lib/axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ArrowLeft, User, Mail, Calendar, CheckCircle, XCircle } from 'lucide-react';
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
}

export default function ContactListDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const [contacts, setContacts] = useState<Contact[]>([]);
    const [listInfo, setListInfo] = useState<ContactList | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const fetchData = async () => {
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
    };

    useEffect(() => {
        fetchData();

        const handleRefresh = () => fetchData();
        window.addEventListener('agent-action-completed', handleRefresh);
        return () => window.removeEventListener('agent-action-completed', handleRefresh);
    }, [id]);

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
