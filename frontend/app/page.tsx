import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { 
  ArrowRight, 
  CheckCircle, 
  Mail, 
  BarChart3, 
  Zap, 
  Shield, 
  Users, 
  Sparkles,
  Globe,
  TrendingUp,
  Clock,
  Target,
  Star,
  ChevronRight
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
          <Link href="/" className="flex items-center gap-2.5 font-bold text-xl transition-transform hover:scale-105">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl gradient-bg">
              <Mail className="h-5 w-5 text-white" />
            </div>
            <span className="hidden sm:inline-block">EmailCampaign</span>
          </Link>
          <nav className="flex items-center gap-2 sm:gap-4">
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
        <section className="relative overflow-hidden py-20 sm:py-28 lg:py-36">
          {/* Background decoration */}
          <div className="absolute inset-0 -z-10">
            <div className="absolute left-1/2 top-0 -translate-x-1/2 -translate-y-1/2 h-[600px] w-[600px] rounded-full bg-primary/10 blur-[120px]" />
            <div className="absolute right-0 top-1/2 h-[400px] w-[400px] rounded-full bg-purple-500/10 blur-[100px]" />
            <div className="absolute left-0 bottom-0 h-[300px] w-[300px] rounded-full bg-blue-500/10 blur-[80px]" />
          </div>
          
          <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col items-center text-center">
              {/* Badge */}
              <div className="animate-fade-in mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-muted/50 px-4 py-1.5 text-sm font-medium text-muted-foreground backdrop-blur-sm">
                <Sparkles className="h-4 w-4 text-primary" />
                <span>Now with AI-Powered Campaign Optimization</span>
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

        {/* Features Section */}
        <section className="py-20 sm:py-28 lg:py-36">
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
                    "{testimonial.quote}"
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
        <section className="relative overflow-hidden py-20 sm:py-28">
          <div className="absolute inset-0 -z-10">
            <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[500px] w-[500px] rounded-full bg-primary/20 blur-[120px]" />
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
              <Link href="/" className="flex items-center gap-2.5 font-bold text-xl">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl gradient-bg">
                  <Mail className="h-5 w-5 text-white" />
                </div>
                <span>EmailCampaign</span>
              </Link>
              <p className="mt-4 text-sm text-muted-foreground">
                Modern email marketing platform for organizations that want to grow.
              </p>
            </div>
            <div>
              <h4 className="mb-4 text-sm font-semibold">Product</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link href="#" className="transition-colors hover:text-foreground">Features</Link></li>
                <li><Link href="#" className="transition-colors hover:text-foreground">Pricing</Link></li>
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
