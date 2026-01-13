'use client';

import { useCallback, useEffect, useState, use } from 'react';
import Link from 'next/link';
import api from '@/config/axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  ArrowLeft, Mail, Calendar, CheckCircle, XCircle, Copy, Check, 
  Link as LinkIcon, Plus, MoreHorizontal, Edit, Trash2, Search,
  AlertTriangle, UserPlus, Phone, ToggleLeft, ToggleRight
} from 'lucide-react';
import { toast } from 'sonner';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface Contact {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
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
  const [searchQuery, setSearchQuery] = useState('');

  // Add contact dialog state
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [newFirstName, setNewFirstName] = useState('');
  const [newLastName, setNewLastName] = useState('');
  const [newPhone, setNewPhone] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  // Edit contact dialog state
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [contactToEdit, setContactToEdit] = useState<Contact | null>(null);
  const [editEmail, setEditEmail] = useState('');
  const [editFirstName, setEditFirstName] = useState('');
  const [editLastName, setEditLastName] = useState('');
  const [editPhone, setEditPhone] = useState('');
  const [editStatus, setEditStatus] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);

  // Delete contact dialog state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [contactToDelete, setContactToDelete] = useState<Contact | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Edit list dialog state
  const [editListDialogOpen, setEditListDialogOpen] = useState(false);
  const [editListName, setEditListName] = useState('');
  const [editListDescription, setEditListDescription] = useState('');
  const [isUpdatingList, setIsUpdatingList] = useState(false);

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
      const contactsData = Array.isArray(contactsResponse.data) 
        ? contactsResponse.data 
        : (contactsResponse.data.data || []);
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

  // Filter contacts by search
  const filteredContacts = contacts.filter(contact =>
    contact.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    contact.first_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    contact.last_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Add contact handler
  const handleAddContact = async () => {
    if (!newEmail.trim()) {
      toast.error('Email is required');
      return;
    }

    setIsAdding(true);
    try {
      await api.post('/campaigns/contacts/', {
        email: newEmail.trim(),
        first_name: newFirstName.trim(),
        last_name: newLastName.trim(),
        phone: newPhone.trim(),
        list_ids: [id],
      });
      toast.success('Contact added successfully');
      fetchData();
      setAddDialogOpen(false);
      setNewEmail('');
      setNewFirstName('');
      setNewLastName('');
      setNewPhone('');
    } catch (error: any) {
      console.error(error);
      toast.error(error?.response?.data?.detail || error?.response?.data?.email?.[0] || 'Failed to add contact');
    } finally {
      setIsAdding(false);
    }
  };

  // Edit contact handlers
  const handleEditClick = (contact: Contact) => {
    setContactToEdit(contact);
    setEditEmail(contact.email);
    setEditFirstName(contact.first_name || '');
    setEditLastName(contact.last_name || '');
    setEditPhone(contact.phone || '');
    setEditStatus(contact.status || 'ACTIVE');
    setEditDialogOpen(true);
  };

  const handleEditConfirm = async () => {
    if (!contactToEdit || !editEmail.trim()) return;

    setIsUpdating(true);
    try {
      await api.put(`/campaigns/contacts/${contactToEdit.id}/`, {
        email: editEmail.trim(),
        first_name: editFirstName.trim(),
        last_name: editLastName.trim(),
        phone: editPhone.trim(),
      });
      toast.success('Contact updated successfully');
      fetchData();
    } catch (error: any) {
      console.error(error);
      toast.error(error?.response?.data?.detail || 'Failed to update contact');
    } finally {
      setIsUpdating(false);
      setEditDialogOpen(false);
      setContactToEdit(null);
    }
  };

  // Delete contact handlers
  const handleDeleteClick = (contact: Contact) => {
    setContactToDelete(contact);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!contactToDelete) return;

    setIsDeleting(true);
    try {
      await api.delete(`/campaigns/contacts/${contactToDelete.id}/`);
      toast.success('Contact deleted successfully');
      fetchData();
    } catch (error: any) {
      console.error(error);
      toast.error(error?.response?.data?.detail || 'Failed to delete contact');
    } finally {
      setIsDeleting(false);
      setDeleteDialogOpen(false);
      setContactToDelete(null);
    }
  };

  // Toggle contact status handler
  const handleToggleStatus = async (contact: Contact) => {
    try {
      const response = await api.post(`/campaigns/contacts/${contact.id}/toggle-status/`);
      toast.success(response.data.message || 'Status updated');
      fetchData();
    } catch (error: any) {
      console.error(error);
      toast.error(error?.response?.data?.detail || 'Failed to toggle status');
    }
  };

  // Edit list handlers
  const handleEditListClick = () => {
    if (!listInfo) return;
    setEditListName(listInfo.name);
    setEditListDescription(listInfo.description || '');
    setEditListDialogOpen(true);
  };

  const handleEditListConfirm = async () => {
    if (!editListName.trim()) return;

    setIsUpdatingList(true);
    try {
      await api.put(`/campaigns/contact-lists/${id}/`, {
        name: editListName.trim(),
        description: editListDescription.trim(),
      });
      toast.success('Contact list updated');
      fetchData();
    } catch (error: any) {
      console.error(error);
      toast.error(error?.response?.data?.detail || 'Failed to update list');
    } finally {
      setIsUpdatingList(false);
      setEditListDialogOpen(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
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
            <p className="text-muted-foreground">
              {listInfo?.description || 'View and manage contacts in this list.'}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleEditListClick}>
            <Edit className="mr-2 h-4 w-4" />
            Edit List
          </Button>
          <Button onClick={() => setAddDialogOpen(true)} className="gradient-bg border-0 text-white">
            <UserPlus className="mr-2 h-4 w-4" />
            Add Contact
          </Button>
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

      {/* Contacts Card */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <CardTitle className="text-xl font-semibold flex items-center gap-2">
              Contacts ({contacts.length})
            </CardTitle>
            <div className="relative max-w-sm">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search contacts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Email</TableHead>
                    <TableHead>First Name</TableHead>
                    <TableHead>Last Name</TableHead>
                    <TableHead>Phone</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Joined</TableHead>
                    <TableHead className="w-[50px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredContacts.map((contact) => (
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
                        {contact.phone ? (
                          <div className="flex items-center gap-1">
                            <Phone className="h-3 w-3 text-muted-foreground" />
                            {contact.phone}
                          </div>
                        ) : '-'}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          {contact.status === 'ACTIVE' || contact.is_active ? (
                            <>
                              <CheckCircle className="h-4 w-4 text-green-500" />
                              <span className="text-green-700 capitalize text-sm">{contact.status?.toLowerCase() || 'active'}</span>
                            </>
                          ) : (
                            <>
                              <XCircle className="h-4 w-4 text-red-500" />
                              <span className="text-red-700 capitalize text-sm">{contact.status?.toLowerCase() || 'inactive'}</span>
                            </>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 text-muted-foreground text-sm">
                          <Calendar className="h-4 w-4" />
                          {contact.created_at ? new Date(contact.created_at).toLocaleDateString() : '-'}
                        </div>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem 
                              className="gap-2"
                              onClick={() => handleToggleStatus(contact)}
                            >
                              {contact.status === 'ACTIVE' ? (
                                <>
                                  <ToggleRight className="h-4 w-4" />
                                  Deactivate
                                </>
                              ) : (
                                <>
                                  <ToggleLeft className="h-4 w-4" />
                                  Activate
                                </>
                              )}
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              className="gap-2"
                              onClick={() => handleEditClick(contact)}
                            >
                              <Edit className="h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem 
                              className="gap-2 text-destructive focus:text-destructive"
                              onClick={() => handleDeleteClick(contact)}
                            >
                              <Trash2 className="h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                  {filteredContacts.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} className="h-32 text-center text-muted-foreground">
                        {searchQuery ? 'No contacts match your search.' : 'No contacts found in this list.'}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add Contact Dialog */}
      <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New Contact</DialogTitle>
            <DialogDescription>
              Add a new contact to this list. Email is required.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="new-email">Email *</Label>
              <Input
                id="new-email"
                type="email"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                placeholder="john@example.com"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="new-first-name">First Name</Label>
                <Input
                  id="new-first-name"
                  value={newFirstName}
                  onChange={(e) => setNewFirstName(e.target.value)}
                  placeholder="John"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new-last-name">Last Name</Label>
                <Input
                  id="new-last-name"
                  value={newLastName}
                  onChange={(e) => setNewLastName(e.target.value)}
                  placeholder="Doe"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-phone">Phone</Label>
              <Input
                id="new-phone"
                type="tel"
                value={newPhone}
                onChange={(e) => setNewPhone(e.target.value)}
                placeholder="+1 234 567 8900"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddDialogOpen(false)} disabled={isAdding}>
              Cancel
            </Button>
            <Button onClick={handleAddContact} disabled={isAdding || !newEmail.trim()}>
              {isAdding ? 'Adding...' : 'Add Contact'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Contact Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Contact</DialogTitle>
            <DialogDescription>
              Update the contact information.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-email">Email *</Label>
              <Input
                id="edit-email"
                type="email"
                value={editEmail}
                onChange={(e) => setEditEmail(e.target.value)}
                placeholder="john@example.com"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit-first-name">First Name</Label>
                <Input
                  id="edit-first-name"
                  value={editFirstName}
                  onChange={(e) => setEditFirstName(e.target.value)}
                  placeholder="John"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-last-name">Last Name</Label>
                <Input
                  id="edit-last-name"
                  value={editLastName}
                  onChange={(e) => setEditLastName(e.target.value)}
                  placeholder="Doe"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-phone">Phone</Label>
              <Input
                id="edit-phone"
                type="tel"
                value={editPhone}
                onChange={(e) => setEditPhone(e.target.value)}
                placeholder="+1 234 567 8900"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)} disabled={isUpdating}>
              Cancel
            </Button>
            <Button onClick={handleEditConfirm} disabled={isUpdating || !editEmail.trim()}>
              {isUpdating ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Contact Confirmation */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
                <AlertTriangle className="h-6 w-6 text-destructive" />
              </div>
              <div>
                <AlertDialogTitle>Delete Contact</AlertDialogTitle>
                <AlertDialogDescription>
                  Are you sure you want to delete &quot;{contactToDelete?.email}&quot;? 
                  This action cannot be undone.
                </AlertDialogDescription>
              </div>
            </div>
          </AlertDialogHeader>
          <AlertDialogFooter className="mt-4">
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleDeleteConfirm}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Edit List Dialog */}
      <Dialog open={editListDialogOpen} onOpenChange={setEditListDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Contact List</DialogTitle>
            <DialogDescription>
              Update the name and description of this contact list.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-list-name">List Name</Label>
              <Input
                id="edit-list-name"
                value={editListName}
                onChange={(e) => setEditListName(e.target.value)}
                placeholder="e.g., Newsletter Subscribers"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-list-description">Description (Optional)</Label>
              <Input
                id="edit-list-description"
                value={editListDescription}
                onChange={(e) => setEditListDescription(e.target.value)}
                placeholder="e.g., Users who signed up via website"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditListDialogOpen(false)} disabled={isUpdatingList}>
              Cancel
            </Button>
            <Button onClick={handleEditListConfirm} disabled={isUpdatingList || !editListName.trim()}>
              {isUpdatingList ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
