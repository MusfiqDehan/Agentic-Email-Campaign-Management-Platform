'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/config/axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus, Users, Upload, Search, UserCheck, ArrowUpRight } from 'lucide-react';
import { toast } from 'sonner';
import { Input } from '@/components/ui/input';

interface ContactList {
  id: string;
  name: string;
  total_contacts: number;
  active_contacts: number;
  created_at: string;
}

export default function ContactsPage() {
  const [lists, setLists] = useState<ContactList[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

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
            <Link key={list.id} href={`/dashboard/contacts/${list.id}`}>
              <Card className="group h-full cursor-pointer overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10 transition-transform group-hover:scale-110">
                        <Users className="h-5 w-5 text-blue-500" />
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
                    <ArrowUpRight className="h-4 w-4 text-muted-foreground opacity-0 transition-all group-hover:opacity-100" />
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex gap-4">
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
            </Link>
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
    </div>
  );
}
