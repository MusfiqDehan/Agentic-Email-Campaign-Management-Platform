'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/config/axios';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Loader2, Upload, Building, User as UserIcon, Camera } from 'lucide-react';

export default function ProfilePage() {
    const { user, refreshUser } = useAuth();
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [profileData, setProfileData] = useState<any>(null);

    const profileInputRef = useRef<HTMLInputElement>(null);
    const logoInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        fetchProfile();
    }, []);

    const fetchProfile = async () => {
        setIsLoading(true);
        try {
            const response = await api.get('/auth/profile/details/');
            setProfileData(response.data.data);
        } catch (error) {
            toast.error('Failed to load profile details');
        } finally {
            setIsLoading(false);
        }
    };

    const handleUpdateProfile = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSaving(true);

        // We use FormData for image uploads
        const formData = new FormData();
        formData.append('first_name', profileData.first_name);
        formData.append('last_name', profileData.last_name);
        formData.append('phone_number', profileData.phone_number || '');
        formData.append('occupation', profileData.occupation || '');
        formData.append('country', profileData.country || '');
        formData.append('city', profileData.city || '');
        formData.append('address', profileData.address || '');

        try {
            await api.patch('/auth/profile/details/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            toast.success('Profile updated successfully');
            refreshUser();
            fetchProfile();
        } catch (error) {
            toast.error('Failed to update profile');
        } finally {
            setIsSaving(false);
        }
    };

    const handleUpdateOrganization = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSaving(true);

        const formData = new FormData();
        formData.append('name', profileData.organization_details?.name || '');
        formData.append('description', profileData.organization_details?.description || '');

        try {
            await api.patch('/auth/profile/details/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            toast.success('Organization updated successfully');
            fetchProfile();
        } catch (error) {
            toast.error('Failed to update organization');
        } finally {
            setIsSaving(false);
        }
    };

    const handleImageUpload = async (type: 'profile' | 'logo', file: File) => {
        const formData = new FormData();
        if (type === 'profile') {
            formData.append('profile_picture', file);
        } else {
            formData.append('logo', file);
        }

        try {
            await api.patch('/auth/profile/details/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            toast.success(`${type === 'profile' ? 'Profile picture' : 'Logo'} updated`);
            fetchProfile();
            if (type === 'profile') refreshUser();
        } catch (error) {
            toast.error('Failed to upload image');
        }
    };

    if (isLoading) {
        return (
            <div className="flex h-[80vh] items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <div className="relative">
                        <div className="h-16 w-16 rounded-full border-4 border-primary/20" />
                        <div className="absolute inset-0 h-16 w-16 animate-spin rounded-full border-4 border-transparent border-t-primary" />
                    </div>
                    <p className="text-sm text-muted-foreground animate-pulse">Loading profile...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto space-y-6 sm:space-y-8">
            <div>
                <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">Settings</h2>
                <p className="mt-1 text-muted-foreground">
                    Manage your account settings and preferences
                </p>
            </div>

            <Tabs defaultValue="personal" className="space-y-6">
                <TabsList className="grid w-full grid-cols-2 lg:w-auto lg:inline-flex">
                    <TabsTrigger value="personal" className="flex items-center justify-center gap-2">
                        <UserIcon className="h-4 w-4" />
                        <span className="hidden sm:inline">Personal</span> Profile
                    </TabsTrigger>
                    <TabsTrigger value="organization" className="flex items-center justify-center gap-2">
                        <Building className="h-4 w-4" /> Organization
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="personal">
                    <Card className="border-border/50 shadow-lg shadow-black/5">
                        <CardHeader className="pb-4">
                            <CardTitle className="flex items-center gap-2">
                                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                                    <UserIcon className="h-4 w-4 text-primary" />
                                </div>
                                Personal Information
                            </CardTitle>
                            <CardDescription>
                                Update your personal details and how others see you.
                            </CardDescription>
                        </CardHeader>
                        <form onSubmit={handleUpdateProfile}>
                            <CardContent className="space-y-6">
                                <div className="flex flex-col items-center sm:flex-row sm:items-start gap-6 rounded-xl bg-muted/30 p-4">
                                    <div className="relative group">
                                        <Avatar className="h-24 w-24 border-4 border-background shadow-lg transition-transform group-hover:scale-105">
                                            <AvatarImage
                                                src={profileData.profile_picture}
                                                onError={(e) => {
                                                    console.error('Profile image fail', profileData.profile_picture);
                                                }}
                                            />
                                            <AvatarFallback className="text-2xl gradient-bg text-white">
                                                {profileData.first_name?.[0]}{profileData.last_name?.[0]}
                                            </AvatarFallback>
                                        </Avatar>
                                        <button
                                            type="button"
                                            onClick={() => profileInputRef.current?.click()}
                                            className="absolute inset-0 flex items-center justify-center bg-black/40 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                                        >
                                            <Camera className="h-6 w-6" />
                                        </button>
                                        <input
                                            type="file"
                                            ref={profileInputRef}
                                            className="hidden"
                                            accept="image/*"
                                            onChange={(e) => {
                                                const file = e.target.files?.[0];
                                                if (file) handleImageUpload('profile', file);
                                            }}
                                        />
                                    </div>
                                    <div className="flex-1 space-y-1">
                                        <h3 className="font-medium">{profileData.first_name} {profileData.last_name}</h3>
                                        <p className="text-sm text-muted-foreground">{profileData.email}</p>
                                        <p className="text-xs text-muted-foreground mt-2">
                                            JPEG, PNG or WebP. Max size 2MB.
                                        </p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="firstName">First Name</Label>
                                        <Input
                                            id="firstName"
                                            value={profileData.first_name}
                                            onChange={(e) => setProfileData({ ...profileData, first_name: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="lastName">Last Name</Label>
                                        <Input
                                            id="lastName"
                                            value={profileData.last_name}
                                            onChange={(e) => setProfileData({ ...profileData, last_name: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="email">Email Address</Label>
                                        <Input id="email" value={profileData.email} disabled className="bg-muted" />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="phone">Phone Number</Label>
                                        <Input
                                            id="phone"
                                            value={profileData.phone_number || ''}
                                            onChange={(e) => setProfileData({ ...profileData, phone_number: e.target.value })}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="occupation">Occupation</Label>
                                        <Input
                                            id="occupation"
                                            value={profileData.occupation || ''}
                                            onChange={(e) => setProfileData({ ...profileData, occupation: e.target.value })}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="country">Country</Label>
                                        <Input
                                            id="country"
                                            value={profileData.country || ''}
                                            onChange={(e) => setProfileData({ ...profileData, country: e.target.value })}
                                        />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="address">Address</Label>
                                    <Textarea
                                        id="address"
                                        value={profileData.address || ''}
                                        onChange={(e) => setProfileData({ ...profileData, address: e.target.value })}
                                        rows={3}
                                    />
                                </div>
                            </CardContent>
                            <CardFooter className="justify-end space-x-2 border-t pt-6">
                                <Button 
                                    type="submit" 
                                    disabled={isSaving}
                                    className="gradient-bg border-0 text-white shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30"
                                >
                                    {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                    Save Changes
                                </Button>
                            </CardFooter>
                        </form>
                    </Card>
                </TabsContent>

                <TabsContent value="organization">
                    <Card className="border-border/50 shadow-lg shadow-black/5">
                        <CardHeader className="pb-4">
                            <CardTitle className="flex items-center gap-2">
                                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-500/10">
                                    <Building className="h-4 w-4 text-purple-500" />
                                </div>
                                Organization Details
                            </CardTitle>
                            <CardDescription>
                                Manage your organization's public profile and branding.
                            </CardDescription>
                        </CardHeader>
                        <form onSubmit={handleUpdateOrganization}>
                            <CardContent className="space-y-6">
                                <div className="flex flex-col items-center sm:flex-row sm:items-start gap-6 rounded-xl bg-muted/30 p-4">
                                    <div className="relative group rounded-xl border-2 border-dashed border-border p-3 bg-background transition-all hover:border-primary/50">
                                        <img
                                            src={profileData.organization_details?.logo || '/placeholder-logo.png'}
                                            alt="Org Logo"
                                            className="h-24 w-24 object-contain"
                                            onError={(e) => {
                                                (e.target as HTMLImageElement).src = 'https://placehold.co/100x100?text=Logo'
                                            }}
                                        />
                                        <button
                                            type="button"
                                            onClick={() => logoInputRef.current?.click()}
                                            className="absolute inset-0 flex items-center justify-center bg-black/40 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                                        >
                                            <Camera className="h-6 w-6" />
                                        </button>
                                        <input
                                            type="file"
                                            ref={logoInputRef}
                                            className="hidden"
                                            accept="image/*"
                                            onChange={(e) => {
                                                const file = e.target.files?.[0];
                                                if (file) handleImageUpload('logo', file);
                                            }}
                                        />
                                    </div>
                                    <div className="flex-1 space-y-1">
                                        <h3 className="font-medium">{profileData.organization_details?.name || 'My Organization'}</h3>
                                        <p className="text-sm text-muted-foreground">URL Slug: {profileData.organization_details?.slug || 'n/a'}</p>
                                        <p className="text-xs text-muted-foreground mt-2">
                                            Transparent PNG or SVG recommended.
                                        </p>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="orgName">Organization Name</Label>
                                    <Input
                                        id="orgName"
                                        value={profileData.organization_details?.name || ''}
                                        onChange={(e) => setProfileData({
                                            ...profileData,
                                            organization_details: { ...(profileData.organization_details || {}), name: e.target.value }
                                        })}
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="orgDesc">Description</Label>
                                    <Textarea
                                        id="orgDesc"
                                        value={profileData.organization_details?.description || ''}
                                        onChange={(e) => setProfileData({
                                            ...profileData,
                                            organization_details: { ...(profileData.organization_details || {}), description: e.target.value }
                                        })}
                                        placeholder="Tell us about your organization..."
                                        rows={4}
                                    />
                                </div>
                            </CardContent>
                            <CardFooter className="justify-end border-t pt-6">
                                <Button 
                                    type="submit" 
                                    disabled={isSaving || !user?.is_org_admin}
                                    className={user?.is_org_admin ? "gradient-bg border-0 text-white shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30" : ""}
                                >
                                    {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                    {user?.is_org_admin ? 'Update Organization' : 'Admin Only'}
                                </Button>
                            </CardFooter>
                        </form>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
