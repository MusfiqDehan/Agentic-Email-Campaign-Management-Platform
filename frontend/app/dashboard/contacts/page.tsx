'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus, Users, Upload } from 'lucide-react';
import { toast } from 'sonner';

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

  const fetchLists = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/campaigns/contact-lists/');
      setLists(response.data);
    } catch (error) {
      console.error(error);
      toast.error('Failed to fetch contact lists');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLists();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Audience</h2>
          <p className="text-muted-foreground">Manage your contact lists and subscribers.</p>
        </div>
        <div className="flex gap-2">
          <Link href="/dashboard/contacts/import">
            <Button variant="outline">
              <Upload className="mr-2 h-4 w-4" /> Import CSV
            </Button>
          </Link>
          <Link href="/dashboard/contacts/new">
            <Button>
              <Plus className="mr-2 h-4 w-4" /> Create List
            </Button>
          </Link>
        </div>
      </div>

      {isLoading ? (
        <div>Loading...</div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {lists.map((list) => (
            <Card key={list.id} className="hover:bg-gray-50 transition-colors">
              <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                <div className="space-y-1">
                  <CardTitle className="text-base font-medium flex items-center gap-2">
                    <Users className="h-4 w-4 text-primary" />
                    {list.name}
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <div className="mt-2 space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Total Contacts</span>
                    <span className="font-medium">{list.total_contacts}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Active</span>
                    <span className="font-medium text-green-600">{list.active_contacts}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          {lists.length === 0 && (
            <div className="col-span-full flex h-32 items-center justify-center rounded-lg border border-dashed">
              <p className="text-muted-foreground">No contact lists found.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
