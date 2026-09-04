'use client';

import { useCallback, useEffect, useMemo, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { BrandLogo } from '@/components/brand-logo';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { CheckCircle2, Loader2, MailX, ShieldCheck, AlertCircle } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1';

type PageState = 'loading' | 'confirm' | 'done' | 'already' | 'error';

interface UnsubscribeInfo {
  email: string;
  first_name?: string;
  status: string;
  already_unsubscribed?: boolean;
  organization_name?: string;
  message?: string;
  error?: string;
}

function UnsubscribeContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token') || '';

  const [state, setState] = useState<PageState>('loading');
  const [info, setInfo] = useState<UnsubscribeInfo | null>(null);
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const greeting = useMemo(() => {
    if (info?.first_name) return `Hi ${info.first_name},`;
    return 'Hello,';
  }, [info?.first_name]);

  const load = useCallback(async () => {
    if (!token) {
      setState('error');
      setErrorMessage('This unsubscribe link is missing a token. Please use the link from your email.');
      return;
    }
    setState('loading');
    try {
      const res = await fetch(`${API_BASE}/campaigns/unsubscribe/?token=${encodeURIComponent(token)}`, {
        method: 'GET',
        headers: { Accept: 'application/json' },
      });
      const data = await res.json();
      if (!res.ok) {
        setState('error');
        setErrorMessage(data.error || data.message || 'This unsubscribe link is invalid or has expired.');
        return;
      }
      setInfo(data);
      if (data.already_unsubscribed || data.status === 'UNSUBSCRIBED') {
        setState('already');
      } else {
        setState('confirm');
      }
    } catch {
      setState('error');
      setErrorMessage('We could not reach the unsubscribe service. Please try again shortly.');
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  const handleConfirm = async () => {
    if (!token) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/campaigns/unsubscribe/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ token, reason: reason.trim() || undefined }),
      });
      const data = await res.json();
      if (!res.ok) {
        setErrorMessage(data.error || data.message || 'Unsubscribe failed. Please try again.');
        setState('error');
        return;
      }
      setInfo((prev) => ({
        ...(prev || { email: data.email, status: 'UNSUBSCRIBED' }),
        email: data.email,
        organization_name: data.organization_name || prev?.organization_name,
        already_unsubscribed: data.already_unsubscribed,
      }));
      setState(data.already_unsubscribed ? 'already' : 'done');
    } catch {
      setErrorMessage('Something went wrong while unsubscribing. Please try again.');
      setState('error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Atmospheric background */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            'radial-gradient(1200px 600px at 10% -10%, rgba(37, 99, 235, 0.18), transparent 55%),' +
            'radial-gradient(900px 500px at 90% 0%, rgba(14, 165, 233, 0.14), transparent 50%),' +
            'linear-gradient(180deg, #f8fafc 0%, #eef2ff 45%, #f8fafc 100%)',
        }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-[0.35]"
        style={{
          backgroundImage:
            'linear-gradient(rgba(15,23,42,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(15,23,42,0.04) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
          maskImage: 'radial-gradient(ellipse at center, black 30%, transparent 75%)',
        }}
      />

      <div className="relative z-10 mx-auto flex min-h-screen max-w-lg flex-col px-4 py-10 sm:py-16">
        <header className="mb-10 flex items-center justify-between animate-[fadeIn_0.6s_ease-out]">
          <BrandLogo size={32} wordmarkClassName="text-base text-slate-900" />
          <span className="text-xs font-medium tracking-wide text-slate-500 uppercase">
            Email preferences
          </span>
        </header>

        <main className="flex flex-1 flex-col justify-center">
          <div
            className="rounded-2xl border border-white/60 bg-white/80 p-8 shadow-[0_24px_80px_-32px_rgba(15,23,42,0.35)] backdrop-blur-md animate-[riseIn_0.7s_ease-out]"
          >
            {state === 'loading' && (
              <div className="flex flex-col items-center gap-4 py-10 text-slate-600">
                <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
                <p className="text-sm">Checking your subscription…</p>
              </div>
            )}

            {(state === 'confirm') && info && (
              <div className="space-y-6">
                <div className="space-y-3">
                  <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-purple-50 text-purple-600">
                    <MailX className="h-6 w-6" />
                  </div>
                  <p className="text-sm font-medium text-slate-500">{greeting}</p>
                  <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
                    {info.organization_name || 'EmailCampaign'}
                  </h1>
                  <p className="text-base leading-relaxed text-slate-600">
                    Unsubscribe <span className="font-medium text-slate-900">{info.email}</span> from
                    future marketing emails. You can resubscribe anytime by contacting the sender.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reason" className="text-slate-700">
                    Reason (optional)
                  </Label>
                  <Textarea
                    id="reason"
                    rows={3}
                    placeholder="Too many emails, content not relevant, …"
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    className="resize-none bg-white"
                  />
                </div>

                <div className="flex flex-col gap-3 sm:flex-row">
                  <Button
                    onClick={handleConfirm}
                    disabled={submitting}
                    className="flex-1 bg-slate-900 text-white hover:bg-slate-800"
                  >
                    {submitting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Working…
                      </>
                    ) : (
                      'Confirm unsubscribe'
                    )}
                  </Button>
                  <Button asChild variant="outline" className="flex-1">
                    <Link href="/">Keep me subscribed</Link>
                  </Button>
                </div>

                <p className="flex items-start gap-2 text-xs text-slate-500">
                  <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                  We will stop sending campaign emails to this address. Transactional messages (like
                  password resets) may still be delivered when required.
                </p>
              </div>
            )}

            {(state === 'done' || state === 'already') && info && (
              <div className="space-y-5 text-center animate-[fadeIn_0.5s_ease-out]">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
                  <CheckCircle2 className="h-7 w-7" />
                </div>
                <div className="space-y-2">
                  <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
                    {state === 'already' ? 'Already unsubscribed' : 'You are unsubscribed'}
                  </h1>
                  <p className="text-slate-600">
                    <span className="font-medium text-slate-900">{info.email}</span> will no longer
                    receive marketing emails
                    {info.organization_name ? ` from ${info.organization_name}` : ''}.
                  </p>
                </div>
                <Button asChild variant="outline">
                  <Link href="/">Back to home</Link>
                </Button>
              </div>
            )}

            {state === 'error' && (
              <div className="space-y-5 text-center">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-rose-50 text-rose-600">
                  <AlertCircle className="h-7 w-7" />
                </div>
                <div className="space-y-2">
                  <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
                    Link unavailable
                  </h1>
                  <p className="text-slate-600">{errorMessage}</p>
                </div>
                <Button asChild variant="outline">
                  <Link href="/">Go home</Link>
                </Button>
              </div>
            )}
          </div>
        </main>

        <footer className="mt-10 text-center text-xs text-slate-500 animate-[fadeIn_0.9s_ease-out]">
          Preference center · Powered by EmailCampaign
        </footer>
      </div>

      <style jsx global>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes riseIn {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}

export default function UnsubscribePage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-slate-50 text-slate-600">
          <Loader2 className="h-6 w-6 animate-spin" />
        </div>
      }
    >
      <UnsubscribeContent />
    </Suspense>
  );
}
