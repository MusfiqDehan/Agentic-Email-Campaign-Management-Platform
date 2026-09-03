'use client';

import { useState } from 'react';
import { ChevronLeft, ChevronRight, Star } from 'lucide-react';

const testimonials = [
  {
    quote:
      'AI Email delivery has significantly improved our outreach workflow. EmailCampaign is remarkably easy to use, highly effective, and drove a 37% increase in our primary response rate within the first month.',
    author: 'Sarah West',
    role: 'Marketing Director',
    company: 'GrowthScale Labs',
    stats: '+37% response rate',
    image: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&auto=format&fit=crop&q=80',
  },
  {
    quote:
      'The inbox placement rate and automatic SPF/DKIM verification took away all the technical headaches our sales development team faced previously. We scaled our pipeline 3x.',
    author: 'Michael Ross',
    role: 'Head of Outbound Operations',
    company: 'CloudVentures',
    stats: '3.2x open volume',
    image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&auto=format&fit=crop&q=80',
  },
  {
    quote:
      'Switching our agency clients to EmailCampaign gave us clear real-time analytics and dynamic contact segmentation that actually works. Our clients love the transparent delivery logs.',
    author: 'Elena Rostova',
    role: 'Founder & CEO',
    company: 'Apex Digital Agency',
    stats: '99.4% inbox delivery',
    image: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&auto=format&fit=crop&q=80',
  },
];

export function TestimonialSlider() {
  const [currentIdx, setCurrentIdx] = useState(0);

  const prev = () => {
    setCurrentIdx((i) => (i === 0 ? testimonials.length - 1 : i - 1));
  };

  const next = () => {
    setCurrentIdx((i) => (i === testimonials.length - 1 ? 0 : i + 1));
  };

  const active = testimonials[currentIdx];

  return (
    <div className="mx-auto max-w-5xl rounded-3xl border border-border/80 bg-card p-6 shadow-xl shadow-purple-500/5 sm:p-10 lg:p-12">
      <div className="grid grid-cols-1 items-center gap-8 lg:grid-cols-12 lg:gap-12">
        {/* Left: Quote text + Author + Controls */}
        <div className="flex flex-col justify-between space-y-6 lg:col-span-8">
          <div>
            <div className="inline-flex items-center gap-1 text-amber-400">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className="h-4 w-4 fill-amber-400 text-amber-400" />
              ))}
              <span className="ml-2 rounded-full bg-purple-50 px-2.5 py-0.5 text-xs font-bold text-purple-600 dark:bg-purple-950/60 dark:text-purple-400">
                {active.stats}
              </span>
            </div>

            <blockquote className="mt-4 text-lg font-medium leading-relaxed text-foreground sm:text-xl lg:text-2xl">
              “{active.quote}”
            </blockquote>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-4 border-t border-border/50 pt-6">
            <div>
              <div className="text-base font-bold text-foreground sm:text-lg">{active.author}</div>
              <div className="text-xs text-muted-foreground sm:text-sm">
                {active.role} • <span className="text-foreground/80">{active.company}</span>
              </div>
            </div>

            {/* Slider arrows */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={prev}
                aria-label="Previous testimonial"
                className="flex h-10 w-10 items-center justify-center rounded-full border border-border/70 bg-background text-muted-foreground transition-all hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
              <span className="text-xs font-semibold text-muted-foreground">
                {currentIdx + 1} / {testimonials.length}
              </span>
              <button
                type="button"
                onClick={next}
                aria-label="Next testimonial"
                className="flex h-10 w-10 items-center justify-center rounded-full border border-border/70 bg-background text-muted-foreground transition-all hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500"
              >
                <ChevronRight className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Right: Headshot visual */}
        <div className="flex justify-center lg:col-span-4">
          <div className="relative h-60 w-60 overflow-hidden rounded-2xl shadow-xl ring-4 ring-purple-100 sm:h-72 sm:w-72 lg:h-80 lg:w-80 dark:ring-purple-950/40">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={active.image}
              alt={active.author}
              className="h-full w-full object-cover transition-transform duration-500 hover:scale-105"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
            <div className="absolute bottom-3 left-3 right-3 text-white">
              <p className="text-sm font-bold">{active.author}</p>
              <p className="text-xs text-white/80">{active.company}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
