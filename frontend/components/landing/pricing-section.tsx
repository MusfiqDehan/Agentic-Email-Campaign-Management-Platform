'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/config/utils';

export function PricingSection() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');

  const plans = [
    {
      name: 'Starter',
      description: 'Ideal for early-stage founders and small outreach lists.',
      monthlyPrice: '$0',
      yearlyPrice: '$0',
      period: 'forever',
      features: [
        'Gmail & Outlook SMTP sending',
        'Up to 500 contacts included',
        'Basic template editor',
        'Real-time open & click webhooks',
        'Community support',
      ],
      highlighted: false,
      cta: 'Start for Free',
      href: '/signup',
    },
    {
      name: 'Pro',
      description: 'For scaling teams that need AI personalization and high throughput.',
      monthlyPrice: '$49',
      yearlyPrice: '$39',
      period: '/ month',
      badge: 'Most Popular',
      features: [
        'Everything in Starter',
        'AWS SES & custom SMTP support',
        'Up to 15,000 contacts',
        'AI copywriting & subject line optimizer',
        'Smart timezone delivery',
        'Priority queue & live chat support',
      ],
      highlighted: true,
      cta: 'Start 14-Day Free Trial',
      href: '/signup',
    },
    {
      name: 'Growth',
      description: 'Custom throughput, dedicated IP warm-up, and multi-team seats.',
      monthlyPrice: '$129',
      yearlyPrice: '$99',
      period: '/ month',
      features: [
        'Everything in Pro',
        'Unlimited contact lists',
        '150,000+ monthly emails',
        'Multi-domain DKIM/SPF management',
        'Agentic AI contact management',
        'Dedicated SLA & account manager',
      ],
      highlighted: false,
      cta: 'Scale with Growth',
      href: '/signup',
    },
  ];

  return (
    <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="text-center">
        <span className="inline-block rounded-full bg-purple-50 px-3 py-1 text-xs font-bold uppercase tracking-wider text-purple-600 dark:bg-purple-950/50 dark:text-purple-400">
          Pricing Plans
        </span>
        <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl lg:text-5xl">
          Simple, scalable pricing
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-base text-muted-foreground sm:text-lg">
          Choose a plan that fits your current subscriber size. Upgrade or downgrade anytime with zero hidden fees.
        </p>

        {/* Billing cycle pill toggle */}
        <div className="mt-8 inline-flex items-center rounded-full border border-border/80 bg-muted/40 p-1 text-xs font-semibold sm:text-sm">
          <button
            type="button"
            onClick={() => setBillingCycle('monthly')}
            className={cn(
              'rounded-full px-4 py-1.5 transition-all',
              billingCycle === 'monthly'
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            Billed Monthly
          </button>
          <button
            type="button"
            onClick={() => setBillingCycle('yearly')}
            className={cn(
              'flex items-center gap-1.5 rounded-full px-4 py-1.5 transition-all',
              billingCycle === 'yearly'
                ? 'bg-purple-600 text-white shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            <span>Billed Yearly</span>
            <span className="rounded-full bg-purple-100 px-1.5 py-0.2 text-[10px] font-bold text-purple-700 dark:bg-purple-900 dark:text-purple-200">
              Save 20%
            </span>
          </button>
        </div>
      </div>

      {/* Cards Grid */}
      <div className="mt-14 grid grid-cols-1 gap-6 lg:grid-cols-3 lg:gap-8">
        {plans.map((plan) => {
          const price = billingCycle === 'yearly' ? plan.yearlyPrice : plan.monthlyPrice;
          return (
            <div
              key={plan.name}
              className={cn(
                'relative flex flex-col justify-between rounded-3xl border bg-card p-6 transition-all duration-300 hover:shadow-xl sm:p-8',
                plan.highlighted
                  ? 'border-purple-500 shadow-2xl shadow-purple-500/10 ring-2 ring-purple-500/40 lg:-translate-y-2'
                  : 'border-border/80 hover:border-border'
              )}
            >
              {plan.badge && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-purple-600 to-indigo-600 px-3.5 py-1 text-xs font-bold text-white shadow-md">
                  {plan.badge}
                </div>
              )}

              <div>
                <h3 className="text-xl font-bold text-foreground">{plan.name}</h3>
                <p className="mt-2 text-xs text-muted-foreground sm:text-sm">{plan.description}</p>

                <div className="mt-6 flex items-baseline gap-1 border-b border-border/60 pb-6">
                  <span className="text-4xl font-extrabold tracking-tight text-foreground sm:text-5xl">
                    {price}
                  </span>
                  <span className="text-xs font-medium text-muted-foreground sm:text-sm">
                    {plan.period}
                  </span>
                </div>

                <div className="mt-6">
                  <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Included Features
                  </span>
                  <ul className="mt-3 space-y-3 text-xs sm:text-sm">
                    {plan.features.map((feature, i) => (
                      <li key={i} className="flex items-start gap-2.5">
                        <Check className="mt-0.5 h-4 w-4 shrink-0 text-purple-600" />
                        <span className="text-muted-foreground">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="mt-8 pt-4">
                <Link href={plan.href} className="w-full">
                  <Button
                    className={cn(
                      'w-full rounded-xl py-6 font-semibold transition-all',
                      plan.highlighted
                        ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/25 hover:bg-purple-700 hover:shadow-xl'
                        : 'border-2 border-border/80 bg-background hover:bg-muted'
                    )}
                    variant={plan.highlighted ? 'default' : 'outline'}
                  >
                    {plan.cta}
                  </Button>
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
