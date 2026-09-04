'use client';

import Link from 'next/link';
import {
  ArrowRight,
  Zap,
  Lock,
  Target,
  Sparkles,
  Users,
  CheckCircle2,
  Globe,
  Briefcase,
  ChevronRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { SiteNav } from '@/components/landing/site-nav';
import { DashboardPreview } from '@/components/landing/dashboard-preview';
import { BentoFeatures } from '@/components/landing/bento-features';
import { PricingSection } from '@/components/landing/pricing-section';
import { TestimonialSlider } from '@/components/landing/testimonial-slider';
import { FaqAccordion } from '@/components/landing/faq-accordion';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { BrandLogo } from '@/components/brand-logo';

// Client logos mimicking the social proof row
const clientLogos = [
  { name: 'Village Labs', symbol: 'V' },
  { name: 'Tensilave', symbol: 'T' },
  { name: 'OneCreative', symbol: 'O' },
  { name: 'RespBroadly', symbol: 'R' },
  { name: 'GrowthCurve', symbol: 'G' },
];

// 3 Highlight cards in Features Overview
const highlightPillars = [
  {
    icon: Zap,
    title: 'Get ahead of problems',
    description:
      'Real-time bounce & spam traps prevention. Automated DNS check alerts you before emails start failing.',
    tag: 'Deliverability',
  },
  {
    icon: Globe,
    title: 'Boost uptime & speed',
    description:
      'Global multi-region sending nodes route your campaigns through low-latency mail transit pathways.',
    tag: 'Performance',
  },
  {
    icon: Lock,
    title: 'Designed for privacy',
    description:
      'Zero contact data selling. Bank-grade AES-256 encryption, GDPR, and CAN-SPAM compliance guaranteed.',
    tag: 'Enterprise Security',
  },
];

// Target segments in Growth section
const targetSegments = [
  {
    icon: Target,
    title: 'Sales teams',
    description: 'Personalize cold outreach sequences that bypass spam filters and land executive replies.',
  },
  {
    icon: Users,
    title: 'Recruiters',
    description: 'Reach high-value talent with multi-touch candidate outreach that feels tailored.',
  },
  {
    icon: Sparkles,
    title: 'Startups',
    description: 'Launch transactional updates and product announcements with instant SMTP setup.',
  },
  {
    icon: Briefcase,
    title: 'Agencies',
    description: 'Manage unlimited client domains, sender identities, and deliverability logs in one place.',
  },
];

// 3 Metric sparklines
const growthStats = [
  {
    value: '30%+',
    label: 'Increase in reply rates',
    sublabel: 'compared to standard legacy blast tools',
    sparkline: [20, 35, 45, 60, 55, 75, 90],
  },
  {
    value: '92%',
    label: 'Primary inbox placement rate',
    sublabel: 'across Gmail, Outlook, and corporate mail servers',
    sparkline: [40, 50, 65, 80, 85, 92, 98],
  },
  {
    value: '3.2X',
    label: 'Higher open volume per campaign',
    sublabel: 'driven by AI-optimized send times and personalized subject lines',
    sparkline: [30, 45, 60, 70, 85, 95, 100],
  },
];

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background pb-[calc(4.25rem+env(safe-area-inset-bottom,0px))] lg:pb-0">
      <SiteNav />

      <main id="main-content" tabIndex={-1} className="flex-1 outline-none">
        {/* ================================================================= */}
        {/* 1. HERO SECTION                                                   */}
        {/* ================================================================= */}
        <section className="relative isolate overflow-hidden pt-12 pb-16 sm:pt-20 sm:pb-24 lg:pt-24 lg:pb-28">
          {/* Subtle warm purple ambient glow background */}
          <div className="absolute inset-0 -z-10 overflow-hidden pointer-events-none">
            <div className="absolute left-1/2 top-0 h-[500px] w-[800px] -translate-x-1/2 -translate-y-1/4 rounded-full bg-purple-500/10 blur-[130px] dark:bg-purple-950/20" />
            <div className="absolute right-0 top-1/3 h-[350px] w-[350px] rounded-full bg-indigo-500/10 blur-[100px] dark:bg-indigo-950/20" />
          </div>

          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col items-center text-center">
              {/* Badge */}
              <div className="animate-fade-in mb-6 inline-flex items-center gap-2 rounded-full border border-purple-200/60 bg-purple-50/80 px-4 py-1.5 text-xs font-semibold text-purple-700 backdrop-blur-sm sm:text-sm dark:border-purple-900/60 dark:bg-purple-950/50 dark:text-purple-300">
                <span className="h-1.5 w-1.5 rounded-full bg-purple-500 animate-pulse" />
                <span>v1.0.0 is now live</span>
                <span className="text-muted-foreground">•</span>
                <span className="font-normal text-muted-foreground">AI-Powered Outreach Platform</span>
                <ChevronRight className="h-3.5 w-3.5 text-purple-600" />
              </div>

              {/* Main Headline */}
              <h1 className="animate-slide-up max-w-4xl text-4xl font-extrabold tracking-tight sm:text-6xl lg:text-7xl">
                Deliver smarter emails with{' '}
                <span className="bg-gradient-to-r from-purple-600 via-indigo-600 to-purple-700 bg-clip-text text-transparent">
                  AI precision
                </span>
              </h1>

              {/* Subheadline */}
              <p
                className="animate-slide-up mt-6 max-w-2xl text-base text-muted-foreground sm:text-lg lg:text-xl"
                style={{ animationDelay: '0.1s' }}
              >
                Reach real inboxes, not spam folders. A complete platform designed to scale your outbound outreach,
                personalize every conversation, and track results in real-time.
              </p>

              {/* CTAs */}
              <div
                className="animate-slide-up mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row sm:gap-5"
                style={{ animationDelay: '0.2s' }}
              >
                <Link href="/signup">
                  <Button
                    size="lg"
                    className="h-13 rounded-full bg-foreground px-8 text-base font-semibold text-background shadow-xl transition-all hover:bg-foreground/90 hover:scale-105"
                  >
                    Get started for free
                  </Button>
                </Link>
                <Link href="#pricing">
                  <Button
                    variant="ghost"
                    size="lg"
                    className="h-13 rounded-full px-6 text-base font-semibold text-foreground hover:bg-muted/60"
                  >
                    <span>View Pricing &amp; Plans</span>
                    <ArrowRight className="ml-2 h-4 w-4 text-purple-600" />
                  </Button>
                </Link>
              </div>

              {/* Product Preview Mockup Window */}
              <div className="animate-scale-in mt-14 w-full" style={{ animationDelay: '0.25s' }}>
                <DashboardPreview />
              </div>

              {/* Social Proof Brand Logos */}
              <div className="mt-16 w-full border-t border-border/50 pt-10">
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Powering delivery for modern teams &amp; agencies worldwide
                </p>
                <div className="mt-6 flex flex-wrap items-center justify-center gap-8 sm:gap-12 lg:gap-16 opacity-70 grayscale transition-all hover:grayscale-0">
                  {clientLogos.map((client) => (
                    <div key={client.name} className="flex items-center gap-2">
                      <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-foreground/10 text-xs font-black text-foreground">
                        {client.symbol}
                      </div>
                      <span className="text-sm font-bold tracking-tight text-foreground">{client.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ================================================================= */}
        {/* 2. THREE-PILLAR OVERVIEW                                          */}
        {/* ================================================================= */}
        <section className="border-t border-border/60 bg-muted/20 py-20 sm:py-24">
          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <span className="inline-block rounded-full bg-purple-50 px-3 py-1 text-xs font-bold uppercase tracking-wider text-purple-600 dark:bg-purple-950/50 dark:text-purple-400">
                Features
              </span>
              <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
                The modern deliverability difference
              </h2>
              <p className="mx-auto mt-3 max-w-2xl text-base text-muted-foreground">
                All your sending infrastructure in one unified platform. Move from guesswork to data-backed inbox delivery.
              </p>
            </div>

            <div className="mt-14 grid grid-cols-1 gap-6 md:grid-cols-3">
              {highlightPillars.map((pillar) => (
                <div
                  key={pillar.title}
                  className="group relative flex flex-col justify-between rounded-3xl border border-border/80 bg-card p-6 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-purple-500/50 hover:shadow-xl sm:p-8"
                >
                  <div>
                    <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-purple-50 text-purple-600 shadow-sm ring-8 ring-purple-50/60 dark:bg-purple-950/50 dark:text-purple-400 dark:ring-purple-950/30">
                      <pillar.icon className="h-7 w-7" />
                    </div>
                    <span className="text-xs font-semibold uppercase tracking-wider text-purple-600 dark:text-purple-400">
                      {pillar.tag}
                    </span>
                    <h3 className="mt-2 text-xl font-bold text-foreground">{pillar.title}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{pillar.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ================================================================= */}
        {/* 3. 2x2 DETAILED BENTO FEATURES                                    */}
        {/* ================================================================= */}
        <section id="features" className="scroll-mt-20 py-20 sm:py-28">
          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <span className="inline-block rounded-full bg-purple-50 px-3 py-1 text-xs font-bold uppercase tracking-wider text-purple-600 dark:bg-purple-950/50 dark:text-purple-400">
                Core Capabilities
              </span>
              <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl lg:text-5xl">
                Powerful features built for modern email outreach
              </h2>
              <p className="mx-auto mt-4 max-w-2xl text-base text-muted-foreground sm:text-lg">
                Equip your marketing and revenue operations with automated lead generation, high-converting copy, and real-time deliverability dashboards.
              </p>
            </div>

            <div className="mt-14">
              <BentoFeatures />
            </div>
          </div>
        </section>

        {/* ================================================================= */}
        {/* 4. GROWTH & SEGMENTS SECTION                                      */}
        {/* ================================================================= */}
        <section id="growth" className="scroll-mt-20 border-t border-border/60 bg-muted/15 py-20 sm:py-28">
          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <span className="inline-block rounded-full bg-purple-50 px-3 py-1 text-xs font-bold uppercase tracking-wider text-purple-600 dark:bg-purple-950/50 dark:text-purple-400">
                Audience &amp; Scale
              </span>
              <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl lg:text-5xl">
                Built for growth-focused teams
              </h2>
              <p className="mx-auto mt-4 max-w-2xl text-base text-muted-foreground sm:text-lg">
                Whether you are a solo founder or managing multi-client campaigns, EmailCampaign adapts to your workflow.
              </p>
            </div>

            {/* 4 Segments (2x2 on tablet/desktop) */}
            <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {targetSegments.map((segment) => (
                <div
                  key={segment.title}
                  className="rounded-2xl border border-border/80 bg-card p-6 shadow-sm transition-all hover:border-purple-500/40 hover:shadow-lg"
                >
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-purple-50 text-purple-600 dark:bg-purple-950/50 dark:text-purple-400">
                    <segment.icon className="h-5 w-5" />
                  </div>
                  <h3 className="mt-4 text-lg font-bold text-foreground">{segment.title}</h3>
                  <p className="mt-2 text-xs leading-relaxed text-muted-foreground sm:text-sm">{segment.description}</p>
                </div>
              ))}
            </div>

            {/* 3 Large Stat Metrics with Sparkline Curves */}
            <div className="mt-12 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {growthStats.map((stat) => (
                <div
                  key={stat.label}
                  className="flex flex-col justify-between rounded-3xl border border-border/80 bg-card p-5 sm:p-7 shadow-sm"
                >
                  <div>
                    <span className="text-3xl font-extrabold tracking-tight text-purple-600 sm:text-4xl lg:text-5xl dark:text-purple-400">
                      {stat.value}
                    </span>
                    <h4 className="mt-2 text-sm sm:text-base font-bold text-foreground">{stat.label}</h4>
                    <p className="mt-1 text-xs text-muted-foreground">{stat.sublabel}</p>
                  </div>

                  {/* Sparkline curve visual */}
                  <div className="mt-5 flex h-12 sm:h-14 items-end gap-1 sm:gap-1.5 border-t border-border/40 pt-3">
                    {stat.sparkline.map((val, idx) => (
                      <div
                        key={idx}
                        className={`flex-1 rounded-t transition-all ${
                          idx === stat.sparkline.length - 1
                            ? 'bg-purple-600 shadow-sm shadow-purple-500/50'
                            : 'bg-purple-200 dark:bg-purple-950/60'
                        }`}
                        style={{ height: `${val}%` }}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ================================================================= */}
        {/* 5. HOW IT WORKS                                                   */}
        {/* ================================================================= */}
        <section id="how-it-works" className="scroll-mt-20 py-20 sm:py-24">
          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <span className="inline-block rounded-full bg-purple-50 px-3 py-1 text-xs font-bold uppercase tracking-wider text-purple-600 dark:bg-purple-950/50 dark:text-purple-400">
                Setup Workflow
              </span>
              <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
                From setup to results in three simple steps
              </h2>
              <p className="mx-auto mt-3 max-w-2xl text-base text-muted-foreground">
                Zero complex configuration. Connect your provider, verify your sender domain, and launch.
              </p>
            </div>

            <div className="mt-14 grid grid-cols-1 gap-8 md:grid-cols-3">
              {[
                {
                  step: '01',
                  title: 'Connect your provider',
                  description:
                    'Link your Gmail, Google Workspace, Outlook, or AWS SES credentials in seconds. Built-in encryption keeps tokens secure.',
                },
                {
                  step: '02',
                  title: 'Build & personalize',
                  description:
                    'Draft campaigns using AI prompt assistance, dynamic contact tags, and verified DKIM/SPF domain tracking.',
                },
                {
                  step: '03',
                  title: 'Send & track results',
                  description:
                    'Schedule delivery for peak open hours, inspect live delivery webhooks, and automate responses without manual work.',
                },
              ].map((item) => (
                <div key={item.step} className="relative rounded-2xl border border-border/80 bg-card p-6 sm:p-8">
                  <span className="text-4xl font-black text-purple-200 sm:text-5xl dark:text-purple-950">
                    {item.step}
                  </span>
                  <h3 className="mt-3 text-lg font-bold text-foreground sm:text-xl">{item.title}</h3>
                  <p className="mt-2 text-xs leading-relaxed text-muted-foreground sm:text-sm">
                    {item.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ================================================================= */}
        {/* 6. TESTIMONIAL SLIDER                                             */}
        {/* ================================================================= */}
        <section className="border-t border-border/60 bg-muted/20 py-20 sm:py-28">
          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mb-12 text-center">
              <span className="inline-block rounded-full bg-purple-50 px-3 py-1 text-xs font-bold uppercase tracking-wider text-purple-600 dark:bg-purple-950/50 dark:text-purple-400">
                Customer Stories
              </span>
              <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
                Hear from our happy users
              </h2>
              <p className="mx-auto mt-3 max-w-xl text-base text-muted-foreground">
                Real feedback from marketing leaders and growth operators scaling outbound revenue.
              </p>
            </div>

            <TestimonialSlider />
          </div>
        </section>

        {/* ================================================================= */}
        {/* 7. PRICING SECTION                                                */}
        {/* ================================================================= */}
        <section id="pricing" className="scroll-mt-20 py-20 sm:py-28">
          <PricingSection />
        </section>

        {/* ================================================================= */}
        {/* 8. FAQ SECTION                                                    */}
        {/* ================================================================= */}
        <section id="faq" className="scroll-mt-20 border-t border-border/60 bg-muted/20 py-20 sm:py-28">
          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mb-12 text-center">
              <span className="inline-block rounded-full bg-purple-50 px-3 py-1 text-xs font-bold uppercase tracking-wider text-purple-600 dark:bg-purple-950/50 dark:text-purple-400">
                Common Questions
              </span>
              <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
                Frequently asked questions
              </h2>
              <p className="mx-auto mt-3 max-w-xl text-base text-muted-foreground">
                Everything you need to know about our deliverability engine, DNS setup, and billing.
              </p>
            </div>

            <FaqAccordion />
          </div>
        </section>

        {/* ================================================================= */}
        {/* 9. BOTTOM CTA PRE-FOOTER                                          */}
        {/* ================================================================= */}
        <section className="relative isolate overflow-hidden bg-gradient-to-b from-card to-background py-20 text-center sm:py-24">
          <div className="container mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
            <h2 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-5xl">
              Ready to transform your email outreach?
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-base text-muted-foreground sm:text-lg">
              Join thousands of growth teams sending targeted campaigns with unmatched deliverability.
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row sm:gap-5">
              <Link href="/signup">
                <Button
                  size="lg"
                  className="h-13 rounded-full bg-purple-600 px-8 text-base font-semibold text-white shadow-xl shadow-purple-500/25 transition-all hover:bg-purple-700 hover:scale-105"
                >
                  Start Your Free Trial
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
              <Link href="/docs">
                <Button variant="outline" size="lg" className="h-13 rounded-full px-7 text-base font-semibold">
                  Read Onboarding Docs
                </Button>
              </Link>
            </div>
            <p className="mt-4 text-xs text-muted-foreground">No credit card required • 14-day free trial • Cancel anytime</p>
          </div>
        </section>
      </main>

      {/* ================================================================= */}
      {/* 10. HIGH-FIDELITY DARK MODERN FOOTER                              */}
      {/* ================================================================= */}
      <footer className="border-t border-zinc-800 bg-zinc-950 text-zinc-300">
        <div className="container mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 gap-10 md:grid-cols-2 lg:grid-cols-5">
            {/* Col 1: Brand & Bio */}
            <div className="lg:col-span-2">
              <Link href="/" className="inline-flex transition-transform hover:scale-105">
                <BrandLogo size={36} wordmarkClassName="text-xl text-white" />
              </Link>
              <p className="mt-4 max-w-sm text-sm leading-relaxed text-zinc-400">
                Deliver smarter emails with AI precision. Next-generation email campaign management, automated DNS deliverability, and verified sender workflows for modern revenue teams.
              </p>
              <div className="mt-6 flex items-center gap-3">
                <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
                <span className="text-xs font-medium text-zinc-400">All systems operational (99.9% SLA)</span>
              </div>
            </div>

            {/* Col 2: Quick Links */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-white">Quick Links</h4>
              <ul className="mt-4 space-y-2.5 text-sm text-zinc-400">
                <li>
                  <Link href="#features" className="transition-colors hover:text-white">
                    Features
                  </Link>
                </li>
                <li>
                  <Link href="#how-it-works" className="transition-colors hover:text-white">
                    How it works
                  </Link>
                </li>
                <li>
                  <Link href="#growth" className="transition-colors hover:text-white">
                    Solutions
                  </Link>
                </li>
                <li>
                  <Link href="#pricing" className="transition-colors hover:text-white">
                    Pricing
                  </Link>
                </li>
                <li>
                  <Link href="#faq" className="transition-colors hover:text-white">
                    FAQ
                  </Link>
                </li>
              </ul>
            </div>

            {/* Col 3: Company */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-white">Company</h4>
              <ul className="mt-4 space-y-2.5 text-sm text-zinc-400">
                <li>
                  <Link href="/docs" className="transition-colors hover:text-white">
                    Documentation
                  </Link>
                </li>
                <li>
                  <Link href="/login" className="transition-colors hover:text-white">
                    Customer Login
                  </Link>
                </li>
                <li>
                  <Link href="/signup" className="transition-colors hover:text-white">
                    Create Account
                  </Link>
                </li>
                <li>
                  <Link href="mailto:support@emailcampaign.io" className="transition-colors hover:text-white">
                    Contact Support
                  </Link>
                </li>
              </ul>
            </div>

            {/* Col 4: Product & Legal */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-white">Product &amp; Trust</h4>
              <ul className="mt-4 space-y-2.5 text-sm text-zinc-400">
                <li>
                  <span className="inline-flex items-center gap-1.5 text-zinc-400">
                    <CheckCircle2 className="h-3.5 w-3.5 text-purple-500" /> GDPR Ready
                  </span>
                </li>
                <li>
                  <span className="inline-flex items-center gap-1.5 text-zinc-400">
                    <CheckCircle2 className="h-3.5 w-3.5 text-purple-500" /> CAN-SPAM Certified
                  </span>
                </li>
                <li>
                  <span className="inline-flex items-center gap-1.5 text-zinc-400">
                    <CheckCircle2 className="h-3.5 w-3.5 text-purple-500" /> AES-256 Encrypted
                  </span>
                </li>
                <li>
                  <span className="inline-flex items-center gap-1.5 text-zinc-400">
                    <CheckCircle2 className="h-3.5 w-3.5 text-purple-500" /> DKIM &amp; SPF Auto
                  </span>
                </li>
              </ul>
            </div>
          </div>

          {/* Bottom sub-footer */}
          <div className="mt-14 flex flex-col items-center justify-between gap-4 border-t border-zinc-800/80 pt-8 sm:flex-row">
            <p className="text-xs text-zinc-500">
              © {new Date().getFullYear()} EmailCampaign Inc. All rights reserved.
            </p>
            <div className="flex items-center gap-4">
              <ThemeToggle className="text-zinc-400 hover:text-white hover:bg-zinc-800" />
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
