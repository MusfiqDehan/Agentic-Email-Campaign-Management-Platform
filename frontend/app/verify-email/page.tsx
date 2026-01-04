'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import api from '@/config/axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import type { AxiosError } from 'axios';

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  const router = useRouter();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Verifying your email...');

  useEffect(() => {
    const verify = async () => {
      if (!token) {
        setStatus('error');
        setMessage('Invalid verification link.');
        return;
      }

      try {
        await api.get(`/auth/verify-email/?token=${token}`);
        setStatus('success');
        setMessage('Email verified successfully! You can now login.');
      } catch (error: unknown) {
        setStatus('error');
        const axiosError = error as AxiosError<{ detail?: string }>;
        setMessage(axiosError.response?.data?.detail || 'Verification failed. The link may be expired.');
      }
    };

    void verify();
  }, [token]);

  return (
    <Card className="w-full max-w-md text-center">
      <CardHeader>
        <CardTitle>Email Verification</CardTitle>
        <CardDescription>
          {status === 'loading' && 'Please wait while we verify your email address.'}
          {status === 'success' && 'Your email has been verified.'}
          {status === 'error' && 'There was a problem verifying your email.'}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col items-center space-y-4">
        {status === 'loading' && (
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
        )}
        {status === 'success' && (
          <>
            <CheckCircle className="h-12 w-12 text-green-500" />
            <p>{message}</p>
            <Button onClick={() => router.push('/login')}>Go to Login</Button>
          </>
        )}
        {status === 'error' && (
          <>
            <XCircle className="h-12 w-12 text-red-500" />
            <p className="text-red-500">{message}</p>
            <Button variant="outline" onClick={() => router.push('/login')}>Back to Login</Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}

export default function VerifyEmailPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <Suspense fallback={<div>Loading...</div>}>
        <VerifyEmailContent />
      </Suspense>
    </div>
  );
}
