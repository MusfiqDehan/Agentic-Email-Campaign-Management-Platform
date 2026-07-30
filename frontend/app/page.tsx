import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { BrandLogo } from '@/components/brand-logo';
import { cn } from '@/config/utils';
import { HeroIllustration } from '@/components/landing/hero-illustration';
import { NetworkBackground } from '@/components/landing/network-background';
import { ProcessConnector } from '@/components/landing/process-connector';
import { GrowthChart } from '@/components/landing/growth-chart';
import {
  ArrowRight,
  Mail,
  BarChart3,
  Zap,
  Shield,
  Users,
  Sparkles,
  Globe,
  Clock,
  Target,
  Star,
  ChevronRight,
  CheckCircle2,
  Check,
  Link2,
  Rocket,
  Building2
} from 'lucide-react';

const features = [
  {
    icon: Zap,
    title: "Lightning Fast Delivery",
    description: "Built for speed with optimized infrastructure ensuring your emails reach inboxes instantly.",
    gradient: "from-yellow-500 to-orange-500"
  },
  {
    icon: BarChart3,
    title: "Real-time Analytics",
    description: "Track opens, clicks, and conversions with beautiful, actionable dashboards and reports.",
    gradient: "from-blue-500 to-cyan-500"
  },
  {
    icon: Shield,
    title: "Enterprise Security",
    description: "Bank-level encryption and compliance with GDPR, CAN-SPAM, and other regulations.",
    gradient: "from-green-500 to-emerald-500"
  },
  {
    icon: Users,
    title: "Smart Segmentation",
    description: "AI-powered audience segmentation for personalized campaigns that convert.",
    gradient: "from-purple-500 to-pink-500"
  },
  {
    icon: Sparkles,
    title: "AI-Powered Content",
    description: "Generate compelling email content with our built-in AI assistant.",
    gradient: "from-indigo-500 to-violet-500"
  },
  {
    icon: Globe,
    title: "Global Reach",
    description: "Send emails worldwide with multi-language support and regional optimization.",
    gradient: "from-rose-500 to-red-500"
  }
];

const stats = [
  { value: "99.9%", label: "Uptime SLA", icon: Clock },
  { value: "50M+", label: "Emails Sent", icon: Mail },
  { value: "10K+", label: "Happy Users", icon: Users },
  { value: "98%", label: "Delivery Rate", icon: Target }
];

const benefits = [
  {
    solution: "One platform for contacts, templates, campaigns & tracking",
    problem: "juggling scattered tools and manual sending"
  },
  {
    solution: "Real-time delivery, open & click analytics on every send",
    problem: "no visibility into what's actually working"
  },
  {
    solution: "AI-personalized content for every audience segment",
    problem: "generic, one-size-fits-all emails"
  },
  {
    solution: "Automation rules handle follow-ups around the clock",
    problem: "hours wasted on repetitive manual outreach"
  }
];

const processSteps = [
  {
    icon: Link2,
    title: "Connect your provider",
    description: "Link Gmail, Outlook, or AWS SES in minutes — no complex setup or developer work required."
  },
  {
    icon: Sparkles,
    title: "Build & personalize",
    description: "Create on-brand campaigns with AI-assisted content and dynamic contact variables."
  },
  {
    icon: Rocket,
    title: "Send, automate & track",
    description: "Launch campaigns, trigger automated follow-ups, and watch real-time analytics roll in."
  }
];

const pricingPlans = [
  {
    name: "Free",
    icon: Mail,
    gradient: "from-slate-400 to-slate-500",
    price: "$0",
    period: "forever",
    description: "Get started with Gmail campaigns — no credit card needed.",
    features: [
      "Gmail & Outlook SMTP sending only",
      "Up to 200 contacts",
      "500 emails / month",
      "1 team member",
      "Basic email templates",
      "Community support"
    ],
    cta: "Start for Free",
    href: "/signup",
    highlighted: false
  },
  {
    name: "Starter",
    icon: Zap,
    gradient: "from-blue-500 to-cyan-500",
    price: "$19",
    period: "/ month",
    description: "For growing teams ready to scale their outreach.",
    features: [
      "Everything in Free",
      "AWS SES provider support",
      "Up to 5,000 contacts",
      "25,000 emails / month",
      "AI-powered template generation",
      "Real-time delivery analytics",
      "3 team members"
    ],
    cta: "Start Free Trial",
    href: "/signup",
    highlighted: false
  },
  {
    name: "Business",
    icon: Rocket,
    gradient: "from-indigo-500 to-purple-500",
    price: "$79",
    period: "/ month",
    description: "For teams that need automation and multi-channel reach.",
    features: [
      "Everything in Starter",
      "SMS campaign automation",
      "Push notifications",
      "Agentic AI contact management",
      "Advanced audience segmentation",
      "Unlimited contacts",
      "150,000 emails / month",
      "10 team members",
      "Priority support"
    ],
    cta: "Start Free Trial",
    href: "/signup",
    highlighted: true,
    badge: "Most Popular"
  },
  {
    name: "Enterprise",
    icon: Building2,
    gradient: "from-orange-500 to-rose-500",
    price: "Custom",
    period: "",
    description: "For organizations with custom needs at scale.",
    features: [
      "Everything in Business",
      "Custom sending volume & infrastructure",
      "Dedicated account manager",
      "Custom SLA & uptime guarantee",
      "SSO & advanced security controls",
      "Custom integrations & onboarding",
      "Unlimited team members"
    ],
    cta: "Contact Sales",
    href: "#contact",
    highlighted: false
  }
];

const testimonials = [
  {
    quote: "EmailCampaign transformed our marketing. We've seen a 3x increase in engagement.",
    author: "Sarah Chen",
    role: "Marketing Director",
    company: "TechCorp",
    avatar: "SC"
  },
  {
    quote: "The analytics alone are worth it. We can finally see what's working in real-time.",
    author: "Michael Ross",
    role: "Growth Lead",
    company: "StartupXYZ",
    avatar: "MR"
  },
  {
    quote: "Switching from our old platform was seamless. The team support is incredible.",
    author: "Emily Johnson",
    role: "CEO",
    company: "Digital Agency",
    avatar: "EJ"
  }
];

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* Navigation */}
      <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link href="/" className="transition-transform hover:scale-105">
            <BrandLogo size={36} wordmarkClassName="hidden sm:inline-block text-xl" priority />
          </Link>
          <nav className="flex items-center gap-2 sm:gap-4">
            <div className="mr-2 hidden items-center gap-6 text-sm font-medium text-muted-foreground md:flex">
              <Link href="#how-it-works" className="transition-colors hover:text-foreground">How it works</Link>
              <Link href="#features" className="transition-colors hover:text-foreground">Features</Link>
              <Link href="#pricing" className="transition-colors hover:text-foreground">Pricing</Link>
            </div>
            <ThemeToggle />
            <Link href="/login">
              <Button variant="ghost" className="hidden sm:inline-flex">
                Log in
              </Button>
            </Link>
            <Link href="/signup">
              <Button className="gradient-bg border-0 text-white shadow-lg shadow-primary/25 transition-all hover:shadow-xl hover:shadow-primary/30 hover:scale-105">
                Get Started
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative isolate overflow-hidden py-20 sm:py-28 lg:py-36">
          {/* Background decoration */}
          <div className="absolute inset-0 -z-10">
            <div className="absolute left-1/2 top-0 -translate-x-1/2 -translate-y-1/2 h-[600px] w-[600px] rounded-full bg-primary/10 blur-[120px]" />
            <div className="absolute right-0 top-1/2 h-[400px] w-[400px] rounded-full bg-purple-500/10 blur-[100px]" />
            <div className="absolute left-0 bottom-0 h-[300px] w-[300px] rounded-full bg-blue-500/10 blur-[80px]" />
          </div>
          
          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid items-center gap-16 lg:grid-cols-[1.05fr_1fr] lg:gap-12">
              <div className="flex flex-col items-center text-center lg:items-start lg:text-left">
                {/* Badge */}
                <div className="animate-fade-in mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-muted/50 px-4 py-1.5 text-sm font-medium text-muted-foreground backdrop-blur-sm">
                  <Sparkles className="h-4 w-4 text-primary" />
                  <span>Now with AI-Powered Agentic Contact Management System</span>
                  <ChevronRight className="h-4 w-4" />
                </div>

                {/* Headline */}
                <h1 className="animate-slide-up max-w-4xl text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl">
                  Email Marketing that
                  <span className="block gradient-text">Actually Works</span>
                </h1>

                {/* Subheadline */}
                <p className="animate-slide-up mt-6 max-w-2xl text-lg text-muted-foreground sm:text-xl" style={{ animationDelay: '0.1s' }}>
                  The modern email campaign platform for growing organizations.
                  Create beautiful campaigns, automate your outreach, and track results — all in one place.
                </p>

                {/* CTA Buttons */}
                <div className="animate-slide-up mt-10 flex flex-col gap-4 sm:flex-row sm:gap-6" style={{ animationDelay: '0.2s' }}>
                  <Link href="/signup">
                    <Button size="lg" className="h-14 px-8 text-base gradient-bg border-0 text-white shadow-xl shadow-primary/25 transition-all hover:shadow-2xl hover:shadow-primary/30 hover:scale-105">
                      Start for Free
                      <ArrowRight className="ml-2 h-5 w-5" />
                    </Button>
                  </Link>
                  <Link href="/login">
                    <Button variant="outline" size="lg" className="h-14 px-8 text-base border-2 bg-background/50 backdrop-blur-sm transition-all hover:bg-accent hover:scale-105">
                      View Demo
                    </Button>
                  </Link>
                </div>

                {/* Social Proof */}
                <div className="animate-fade-in mt-12 flex items-center gap-4 text-sm text-muted-foreground" style={{ animationDelay: '0.3s' }}>
                  <div className="flex -space-x-2">
                    {['bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-orange-500'].map((bg, i) => (
                      <div key={i} className={`h-8 w-8 rounded-full ${bg} border-2 border-background flex items-center justify-center text-xs font-medium text-white`}>
                        {['A', 'B', 'C', 'D'][i]}
                      </div>
                    ))}
                  </div>
                  <div className="flex items-center gap-1">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                  <span>Trusted by 10,000+ marketers</span>
                </div>
              </div>

              {/* Interactive hero illustration */}
              <div className="animate-scale-in" style={{ animationDelay: '0.15s' }}>
                <HeroIllustration />
              </div>
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="border-y border-border bg-muted/30 py-12 sm:py-16">
          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-2 gap-6 md:grid-cols-4 md:gap-8">
              {stats.map((stat, index) => (
                <div key={index} className="flex flex-col items-center text-center">
                  <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                    <stat.icon className="h-6 w-6 text-primary" />
                  </div>
                  <div className="text-3xl font-bold tracking-tight sm:text-4xl gradient-text">{stat.value}</div>
                  <div className="mt-1 text-sm text-muted-foreground">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Benefits Section */}
        <section className="border-t border-border py-20 sm:py-28 lg:py-36">
          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid items-center gap-16 lg:grid-cols-2">
              <div>
                <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-muted/50 px-4 py-1.5 text-sm font-medium text-muted-foreground">
                  <Target className="h-4 w-4 text-primary" />
                  <span>Built for growing teams</span>
                </div>
                <h2 className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
                  Solve real problems,
                  <span className="block gradient-text">not just send emails</span>
                </h2>
                <p className="mt-4 text-lg text-muted-foreground">
                  Most teams don&apos;t struggle with sending emails — they struggle with everything around it:
                  scattered tools, guesswork, and hours of manual work. EmailCampaign fixes that so your
                  business can grow faster with less effort.
                </p>
                <ul className="mt-8 space-y-5">
                  {benefits.map((benefit, index) => (
                    <li key={index} className="flex items-start gap-4">
                      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                        <CheckCircle2 className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="font-semibold">{benefit.solution}</p>
                        <p className="text-sm text-muted-foreground">Instead of {benefit.problem}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>

              <GrowthChart />
            </div>
          </div>
        </section>

        {/* How It Works Section */}
        <section id="how-it-works" className="border-t border-border bg-muted/20 py-20 sm:py-28">
          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
                From setup to results in
                <span className="gradient-text"> three simple steps</span>
              </h2>
              <p className="mx-auto mt-4 max-w-2xl text-lg text-muted-foreground">
                No engineering team required. Most organizations are sending their first campaign the same day.
              </p>
            </div>

            <div className="relative mt-16">
              <div className="pointer-events-none absolute inset-x-[14%] top-8 hidden md:block">
                <ProcessConnector />
              </div>
              <div className="relative grid gap-12 md:grid-cols-3">
                {processSteps.map((step, index) => (
                  <div key={index} className="flex flex-col items-center text-center">
                    <div className="relative z-10 flex h-16 w-16 items-center justify-center rounded-2xl gradient-bg text-white shadow-lg shadow-primary/25">
                      <step.icon className="h-7 w-7" />
                      <span className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full border border-border bg-card text-xs font-bold">
                        {index + 1}
                      </span>
                    </div>
                    <h3 className="mt-5 text-lg font-semibold">{step.title}</h3>
                    <p className="mt-2 max-w-xs text-muted-foreground">{step.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-20 sm:py-28 lg:py-36">
          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
                Everything you need to
                <span className="gradient-text"> succeed</span>
              </h2>
              <p className="mx-auto mt-4 max-w-2xl text-lg text-muted-foreground">
                Powerful features designed to help you create, send, and optimize your email campaigns at scale.
              </p>
            </div>
            
            <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3 stagger-animation">
              {features.map((feature, index) => (
                <div
                  key={index}
                  className="group relative overflow-hidden rounded-2xl border border-border bg-card p-6 transition-all duration-300 hover:border-primary/50 hover:shadow-xl hover:shadow-primary/5 hover:-translate-y-1"
                >
                  <div className={`mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${feature.gradient} shadow-lg`}>
                    <feature.icon className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="mb-2 text-xl font-semibold">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                  
                  {/* Hover gradient effect */}
                  <div className={`absolute inset-0 -z-10 bg-gradient-to-br ${feature.gradient} opacity-0 blur-2xl transition-opacity duration-300 group-hover:opacity-5`} />
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="relative isolate overflow-hidden py-20 sm:py-28 lg:py-36">
          <div className="absolute inset-0 -z-10 opacity-50">
            <NetworkBackground />
          </div>

          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
                Simple pricing that
                <span className="gradient-text"> grows with you</span>
              </h2>
              <p className="mx-auto mt-4 max-w-2xl text-lg text-muted-foreground">
                Start free with Gmail campaigns. Upgrade as your outreach scales — cancel anytime, no surprises.
              </p>
            </div>

            <div className="mt-16 grid items-start gap-6 stagger-animation lg:grid-cols-4">
              {pricingPlans.map((plan, index) => (
                <div
                  key={index}
                  className={cn(
                    "relative flex h-full flex-col rounded-2xl border bg-card p-6 transition-all duration-300 hover:-translate-y-1",
                    plan.highlighted
                      ? "border-primary shadow-2xl shadow-primary/20 ring-2 ring-primary/50 lg:-translate-y-3"
                      : "border-border hover:border-primary/50 hover:shadow-xl hover:shadow-primary/5"
                  )}
                >
                  {plan.badge && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full gradient-bg px-3 py-1 text-xs font-semibold text-white shadow-lg">
                      {plan.badge}
                    </div>
                  )}

                  <div className={`mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${plan.gradient} shadow-lg`}>
                    <plan.icon className="h-6 w-6 text-white" />
                  </div>

                  <h3 className="text-xl font-semibold">{plan.name}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">{plan.description}</p>

                  <div className="mt-6 flex items-baseline gap-1">
                    <span className="text-4xl font-bold tracking-tight">{plan.price}</span>
                    {plan.period && <span className="text-sm text-muted-foreground">{plan.period}</span>}
                  </div>

                  <Link href={plan.href} className="mt-6">
                    <Button
                      className={cn(
                        "w-full",
                        plan.highlighted && "gradient-bg border-0 text-white shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30"
                      )}
                      variant={plan.highlighted ? "default" : "outline"}
                    >
                      {plan.cta}
                    </Button>
                  </Link>

                  <ul className="mt-8 flex-1 space-y-3 text-sm">
                    {plan.features.map((feature, featureIndex) => (
                      <li key={featureIndex} className="flex items-start gap-2">
                        <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                        <span className="text-muted-foreground">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Testimonials Section */}
        <section className="border-t border-border bg-muted/20 py-20 sm:py-28">
          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                Loved by <span className="gradient-text">marketers worldwide</span>
              </h2>
              <p className="mx-auto mt-4 max-w-2xl text-lg text-muted-foreground">
                See why thousands of organizations trust EmailCampaign for their email marketing.
              </p>
            </div>
            
            <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {testimonials.map((testimonial, index) => (
                <div
                  key={index}
                  className="flex flex-col rounded-2xl border border-border bg-card p-6 shadow-sm transition-all duration-300 hover:shadow-lg hover:-translate-y-1"
                >
                  <div className="mb-4 flex items-center gap-1">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                  <blockquote className="flex-1 text-lg leading-relaxed">
                    “{testimonial.quote}”
                  </blockquote>
                  <div className="mt-6 flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full gradient-bg text-sm font-medium text-white">
                      {testimonial.avatar}
                    </div>
                    <div>
                      <div className="font-medium">{testimonial.author}</div>
                      <div className="text-sm text-muted-foreground">
                        {testimonial.role} at {testimonial.company}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="relative isolate overflow-hidden py-20 sm:py-28">
          <div className="absolute inset-0 -z-10">
            <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[500px] w-[500px] rounded-full bg-primary/20 blur-[120px]" />
            <NetworkBackground />
          </div>

          <div className="container mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
              Ready to transform your
              <span className="gradient-text"> email marketing?</span>
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-muted-foreground">
              Join thousands of marketers who are already using EmailCampaign to grow their business.
            </p>
            <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center sm:gap-6">
              <Link href="/signup">
                <Button size="lg" className="h-14 px-10 text-base gradient-bg border-0 text-white shadow-xl shadow-primary/25 transition-all hover:shadow-2xl hover:shadow-primary/30 hover:scale-105">
                  Start Your Free Trial
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <p className="text-sm text-muted-foreground">
                No credit card required • 14-day free trial
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-muted/20">
        <div className="container mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <Link href="/" className="transition-transform hover:scale-105">
                <BrandLogo size={36} wordmarkClassName="text-xl" />
              </Link>
              <p className="mt-4 text-sm text-muted-foreground">
                Modern email marketing platform for organizations that want to grow.
              </p>
            </div>
            <div>
              <h4 className="mb-4 text-sm font-semibold">Product</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link href="#features" className="transition-colors hover:text-foreground">Features</Link></li>
                <li><Link href="#pricing" className="transition-colors hover:text-foreground">Pricing</Link></li>
                <li><Link href="#" className="transition-colors hover:text-foreground">Integrations</Link></li>
                <li><Link href="#" className="transition-colors hover:text-foreground">API</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="mb-4 text-sm font-semibold">Company</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link href="#" className="transition-colors hover:text-foreground">About</Link></li>
                <li><Link href="#" className="transition-colors hover:text-foreground">Blog</Link></li>
                <li><Link href="#" className="transition-colors hover:text-foreground">Careers</Link></li>
                <li><Link href="#" className="transition-colors hover:text-foreground">Contact</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="mb-4 text-sm font-semibold">Legal</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link href="#" className="transition-colors hover:text-foreground">Privacy</Link></li>
                <li><Link href="#" className="transition-colors hover:text-foreground">Terms</Link></li>
                <li><Link href="#" className="transition-colors hover:text-foreground">Security</Link></li>
                <li><Link href="#" className="transition-colors hover:text-foreground">GDPR</Link></li>
              </ul>
            </div>
          </div>
          <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-border pt-8 sm:flex-row">
            <p className="text-sm text-muted-foreground">
              © {new Date().getFullYear()} EmailCampaign Inc. All rights reserved.
            </p>
            <div className="flex items-center gap-4">
              <ThemeToggle />
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
