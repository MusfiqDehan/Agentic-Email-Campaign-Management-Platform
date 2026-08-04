'use client';

import { useCallback, useEffect, useState } from 'react';
import { Loader2, PackagePlus, Pencil, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Package,
  PackageInput,
  createPackage,
  deletePackage,
  fetchPackages,
  updatePackage,
} from '@/services/admin';
import { getApiErrorMessage } from '@/config/api-error';

const NUMBER_FIELDS: Array<{ key: keyof PackageInput; label: string }> = [
  { key: 'contacts_limit', label: 'Contacts limit' },
  { key: 'campaigns_per_month', label: 'Campaigns / month' },
  { key: 'emails_per_day', label: 'Emails / day' },
  { key: 'emails_per_month', label: 'Emails / month' },
  { key: 'emails_per_minute', label: 'Emails / minute' },
  { key: 'batch_size', label: 'Batch size' },
  { key: 'api_requests_per_minute', label: 'API req / minute' },
  { key: 'max_domains', label: 'Max sending domains' },
  { key: 'max_sender_emails', label: 'Max sender emails' },
];

const FLAG_FIELDS: Array<{ key: keyof PackageInput; label: string }> = [
  { key: 'custom_domain_allowed', label: 'Custom domains' },
  { key: 'org_owned_ses_allowed', label: 'Org-owned SES accounts' },
  { key: 'advanced_analytics', label: 'Advanced analytics' },
  { key: 'priority_support', label: 'Priority support' },
  { key: 'bulk_email_allowed', label: 'Bulk email' },
  { key: 'ab_testing_allowed', label: 'A/B testing' },
];

const EMPTY_FORM: PackageInput = {
  name: '',
  display_name: '',
  description: '',
  is_default: false,
  max_domains: 0,
  max_sender_emails: 0,
  custom_domain_allowed: false,
  org_owned_ses_allowed: false,
};

export default function AdminPackagesPage() {
  const [packages, setPackages] = useState<Package[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Package | null>(null);
  const [form, setForm] = useState<PackageInput>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      setPackages(await fetchPackages());
    } catch {
      toast.error('Failed to load packages');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY_FORM);
    setDialogOpen(true);
  };

  const openEdit = (pkg: Package) => {
    setEditing(pkg);
    const form: PackageInput = { ...pkg };
    delete (form as Partial<Package>).id;
    delete (form as Partial<Package>).organization_count;
    setForm(form);
    setDialogOpen(true);
  };

  const handleSave = async () => {
    if (!form.name || !form.display_name) {
      toast.error('Name and display name are required');
      return;
    }
    setSaving(true);
    try {
      if (editing) {
        await updatePackage(editing.id, form);
        toast.success(`Package '${form.name}' updated`);
      } else {
        await createPackage(form);
        toast.success(`Package '${form.name}' created`);
      }
      setDialogOpen(false);
      await load();
    } catch (err: unknown) {
      toast.error(getApiErrorMessage(err, 'Failed to save package'));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (pkg: Package) => {
    if (!confirm(`Delete package '${pkg.name}'?`)) return;
    try {
      await deletePackage(pkg.id);
      toast.success(`Package '${pkg.name}' deleted`);
      await load();
    } catch (err: unknown) {
      toast.error(getApiErrorMessage(err, 'Failed to delete package'));
    }
  };

  const setNumber = (key: keyof PackageInput, raw: string) => {
    setForm((f) => ({ ...f, [key]: raw === '' ? null : Number(raw) }));
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Packages</h1>
          <p className="text-muted-foreground">
            Define subscription tiers — limits and features for each tenant. Empty number = unlimited.
          </p>
        </div>
        <Button onClick={openCreate}>
          <PackagePlus className="h-4 w-4 mr-2" /> New package
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Catalog</CardTitle>
          <CardDescription>Changes apply immediately to every organization on the package.</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Package</TableHead>
                  <TableHead>Domains</TableHead>
                  <TableHead>Sender emails</TableHead>
                  <TableHead>Emails/day</TableHead>
                  <TableHead>Orgs</TableHead>
                  <TableHead>Flags</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {packages.map((pkg) => (
                  <TableRow key={pkg.id}>
                    <TableCell>
                      <span className="font-medium">{pkg.display_name}</span>
                      <span className="text-muted-foreground text-xs ml-2">({pkg.name})</span>
                      {pkg.is_default && <Badge className="ml-2">default</Badge>}
                      {!pkg.is_active && <Badge variant="destructive" className="ml-2">inactive</Badge>}
                    </TableCell>
                    <TableCell>{pkg.max_domains ?? '∞'}</TableCell>
                    <TableCell>{pkg.max_sender_emails ?? '∞'}</TableCell>
                    <TableCell>{pkg.emails_per_day ?? '∞'}</TableCell>
                    <TableCell>{pkg.organization_count ?? 0}</TableCell>
                    <TableCell className="text-xs text-muted-foreground max-w-[220px]">
                      {FLAG_FIELDS.filter((f) => pkg[f.key as keyof Package]).map((f) => f.label).join(', ') || '—'}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button variant="outline" size="sm" onClick={() => openEdit(pkg)}>
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(pkg)}>
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{editing ? `Edit '${editing.name}'` : 'New package'}</DialogTitle>
            <DialogDescription>Leave a number empty for unlimited.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 max-h-[60vh] overflow-auto pr-2">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">Slug</Label>
                <Input
                  id="name"
                  placeholder="growth"
                  value={form.name}
                  disabled={!!editing}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="display_name">Display name</Label>
                <Input
                  id="display_name"
                  placeholder="Growth"
                  value={form.display_name}
                  onChange={(e) => setForm((f) => ({ ...f, display_name: e.target.value }))}
                />
              </div>
            </div>
            <div>
              <Label htmlFor="description">Description</Label>
              <Input
                id="description"
                value={form.description ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-3 gap-3">
              {NUMBER_FIELDS.map(({ key, label }) => (
                <div key={key}>
                  <Label className="text-xs">{label}</Label>
                  <Input
                    type="number"
                    min={0}
                    value={(form[key] as number | null | undefined) ?? ''}
                    onChange={(e) => setNumber(key, e.target.value)}
                  />
                </div>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-2">
              {FLAG_FIELDS.map(({ key, label }) => (
                <label key={key} className="flex items-center gap-2 text-sm">
                  <Checkbox
                    checked={Boolean(form[key])}
                    onCheckedChange={(checked) => setForm((f) => ({ ...f, [key]: checked === true }))}
                  />
                  {label}
                </label>
              ))}
              <label className="flex items-center gap-2 text-sm">
                <Checkbox
                  checked={Boolean(form.is_default)}
                  onCheckedChange={(checked) => setForm((f) => ({ ...f, is_default: checked === true }))}
                />
                Default for new organizations
              </label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              {editing ? 'Save changes' : 'Create package'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
