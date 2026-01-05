'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { usePlatformAdmin } from '@/contexts/AuthContext';
import { Shield } from 'lucide-react';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const isPlatformAdmin = usePlatformAdmin();

  useEffect(() => {
    if (!isPlatformAdmin) {
      router.push('/dashboard');
    }
  }, [isPlatformAdmin, router]);

  if (!isPlatformAdmin) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Shield className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Access Denied</h2>
          <p className="text-muted-foreground">
            You don&apos;t have permission to access this area.
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
