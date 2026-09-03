'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import api from '@/config/axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  Plus, Users, Upload, Search, UserCheck, MoreHorizontal,
  Edit, Trash2, Eye, AlertTriangle
} from 'lucide-react';
import { toast } from 'sonner';
import { Input } from '@/components/ui/input';
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
import { Label } from '@/components/ui/label';

interface ContactList {
  id: string;
  name: string;
  description?: string;
  total_contacts: number;
  active_contacts: number;
  created_at: string;
}

export default function ContactsPage() {
  const router = useRouter();
  const [lists, setLists] = useState<ContactList[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Delete dialog state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [listToDelete, setListToDelete] = useState<ContactList | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  
  // Edit dialog state
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [listToEdit, setListToEdit] = useState<ContactList | null>(null);
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);

  const fetchLists = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/campaigns/contact-lists/');
      const data = Array.isArray(response.data) ? response.data : (response.data.data || []);
      setLists(data);
    } catch (error) {
      console.error(error);
      toast.error('Failed to fetch contact lists');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLists();

    const handleRefresh = () => fetchLists();
    window.addEventListener('agent-action-completed', handleRefresh);
    return () => window.removeEventListener('agent-action-completed', handleRefresh);
  }, []);

  const filteredLists = lists.filter(list =>
    list.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // View list handler
  const handleViewList = (list: ContactList) => {
    router.push(`/dashboard/contacts/${list.id}`);
  };

  // Edit handlers
  const handleEditClick = (list: ContactList) => {
    setListToEdit(list);
    setEditName(list.name);
    setEditDescription(list.description || '');
    setEditDialogOpen(true);
  };

  const handleEditConfirm = async () => {
    if (!listToEdit || !editName.trim()) return;
    
    setIsUpdating(true);
    try {
      await api.put(`/campaigns/contact-lists/${listToEdit.id}/`, {
        name: editName.trim(),
        description: editDescription.trim(),
      });
      toast.success('Contact list updated');
      fetchLists();
    } catch (error: any) {
      console.error(error);
      toast.error(error?.response?.data?.detail || 'Failed to update list');
    } finally {
      setIsUpdating(false);
      setEditDialogOpen(false);
      setListToEdit(null);
    }
  };

  // Delete handlers
  const handleDeleteClick = (list: ContactList) => {
    setListToDelete(list);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!listToDelete) return;
    
    setIsDeleting(true);
    try {
      await api.delete(`/campaigns/contact-lists/${listToDelete.id}/`);
      toast.success('Contact list deleted');
      fetchLists();
    } catch (error: any) {
      console.error(error);
      toast.error(error?.response?.data?.detail || 'Failed to delete list');
    } finally {
      setIsDeleting(false);
      setDeleteDialogOpen(false);
      setListToDelete(null);
    }
  };

  return (
    <div className="space-y-6 sm:space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">Audience</h2>
          <p className="mt-1 text-muted-foreground">
            Manage your contact lists and subscribers
          </p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Link href="/dashboard/contacts/import">
            <Button variant="outline" className="w-full sm:w-auto">
              <Upload className="mr-2 h-4 w-4" />
              Import CSV
            </Button>
          </Link>
          <Link href="/dashboard/contacts/new">
            <Button className="gradient-bg border-0 text-white shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 w-full sm:w-auto">
              <Plus className="mr-2 h-4 w-4" />
              Create List
            </Button>
          </Link>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search contact lists..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Contact Lists Grid */}
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-4 w-1/2 rounded bg-muted" />
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="h-3 w-full rounded bg-muted" />
                  <div className="h-3 w-2/3 rounded bg-muted" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 stagger-animation">
          {filteredLists.map((list) => (
            <Card key={list.id} className="group h-full overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div 
                    className="flex items-center gap-3 flex-1 cursor-pointer"
                    onClick={() => handleViewList(list)}
                  >
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-500/10 transition-transform group-hover:scale-110">
                      <Users className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div>
                      <CardTitle className="text-base font-semibold group-hover:text-primary transition-colors">
                        {list.name}
                      </CardTitle>
                      <p className="text-xs text-muted-foreground">
                        Created {new Date(list.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-8 w-8 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem 
                        className="gap-2"
                        onClick={() => handleViewList(list)}
                      >
                        <Eye className="h-4 w-4" />
                        View Contacts
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        className="gap-2"
                        onClick={() => handleEditClick(list)}
                      >
                        <Edit className="h-4 w-4" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem 
                        className="gap-2 text-destructive focus:text-destructive"
                        onClick={() => handleDeleteClick(list)}
                      >
                        <Trash2 className="h-4 w-4" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div 
                  className="flex gap-4 cursor-pointer"
                  onClick={() => handleViewList(list)}
                >
                  <div className="flex-1 rounded-lg bg-muted/50 p-3 text-center">
                    <div className="flex items-center justify-center gap-1.5">
                      <Users className="h-4 w-4 text-muted-foreground" />
                      <span className="text-lg font-bold">{list.total_contacts}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Total</p>
                  </div>
                  <div className="flex-1 rounded-lg bg-green-500/10 p-3 text-center">
                    <div className="flex items-center justify-center gap-1.5">
                      <UserCheck className="h-4 w-4 text-green-500" />
                      <span className="text-lg font-bold text-green-600 dark:text-green-400">{list.active_contacts}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">Active</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          
          {filteredLists.length === 0 && (
            <Card className="col-span-full">
              <CardContent className="flex flex-col items-center justify-center py-16">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                  <Users className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="mt-4 text-lg font-semibold">No contact lists found</h3>
                <p className="mt-1 text-center text-sm text-muted-foreground max-w-sm">
                  {searchQuery 
                    ? "No lists match your search. Try a different query."
                    : "Create your first contact list to start building your audience."
                  }
                </p>
                {!searchQuery && (
                  <Link href="/dashboard/contacts/new" className="mt-4">
                    <Button className="gradient-bg border-0 text-white">
                      <Plus className="mr-2 h-4 w-4" />
                      Create List
                    </Button>
                  </Link>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Edit List Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Contact List</DialogTitle>
            <DialogDescription>
              Update the name and description of this contact list.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name">List Name</Label>
              <Input
                id="edit-name"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                placeholder="e.g., Newsletter Subscribers"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-description">Description (Optional)</Label>
              <Input
                id="edit-description"
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                placeholder="e.g., Users who signed up via website"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)} disabled={isUpdating}>
              Cancel
            </Button>
            <Button onClick={handleEditConfirm} disabled={isUpdating || !editName.trim()}>
              {isUpdating ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
                <AlertTriangle className="h-6 w-6 text-destructive" />
              </div>
              <div>
                <AlertDialogTitle>Delete Contact List</AlertDialogTitle>
                <AlertDialogDescription>
                  Are you sure you want to delete &quot;{listToDelete?.name}&quot;? 
                  This will also remove all contacts from this list. This action cannot be undone.
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
    </div>
  );
}
