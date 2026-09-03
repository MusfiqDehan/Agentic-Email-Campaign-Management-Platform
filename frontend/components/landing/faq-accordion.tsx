'use client';

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/config/utils';

const faqs = [
  {
    id: 'item-1',
    question: 'How does EmailCampaign improve inbox deliverability?',
    answer:
      'We combine automated DNS configuration checks (SPF, DKIM, and DMARC alignment), real-time bounce-detection webhooks, and IP warm-up protocols. By using custom sender domains and verified credentials like AWS SES or Google Workspace, your emails land directly in inboxes instead of spam or promotion tabs.',
  },
  {
    id: 'item-2',
    question: 'Can I integrate my own custom domain & sending email?',
    answer:
      'Yes! You can connect custom sending domains with dedicated DNS verification records. Once verified, you can create multiple sender addresses (e.g. hello@yourbrand.com, sales@yourbrand.com) and assign them to specific campaigns or team members.',
  },
  {
    id: 'item-3',
    question: 'Do you offer a free trial or free tier?',
    answer:
      'Absolutely. Our Free tier includes 500 emails per month and support for Gmail and Outlook SMTP so you can test campaigns without entering a credit card. You can upgrade to Starter or Business anytime as your subscriber list scales.',
  },
  {
    id: 'item-4',
    question: 'Is my subscriber data safe, encrypted, and GDPR-compliant?',
    answer:
      'Yes. All contact records and sending credentials are encrypted at rest using AES-256 and in transit via TLS 1.3. We offer automated one-click unsubscribe links and complete GDPR/CAN-SPAM compliance out of the box.',
  },
  {
    id: 'item-5',
    question: 'How does the AI copywriting assistant work?',
    answer:
      'The built-in AI assistant helps you craft high-converting subject lines, personalize body paragraphs with dynamic recipient variables (e.g., {{first_name}}, {{company}}), and optimize send schedules based on recipient activity history.',
  },
];

export function FaqAccordion() {
  const [openId, setOpenId] = useState<string | null>('item-1');

  const toggle = (id: string) => {
    setOpenId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="mx-auto max-w-3xl divide-y divide-border/60 rounded-2xl border border-border/80 bg-card shadow-sm">
      {faqs.map((faq) => {
        const isOpen = openId === faq.id;
        return (
          <div key={faq.id} className="transition-colors">
            <button
              type="button"
              onClick={() => toggle(faq.id)}
              aria-expanded={isOpen}
              aria-controls={`faq-answer-${faq.id}`}
              className="flex w-full items-center justify-between p-5 text-left text-base font-semibold text-foreground hover:text-purple-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500/50 sm:p-6"
            >
              <span>{faq.question}</span>
              <span
                className={cn(
                  'ml-4 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-muted/60 text-muted-foreground transition-transform duration-200',
                  isOpen && 'rotate-180 bg-purple-50 text-purple-600 dark:bg-purple-950/60 dark:text-purple-400'
                )}
              >
                <ChevronDown className="h-4 w-4" />
              </span>
            </button>
            {isOpen && (
              <div
                id={`faq-answer-${faq.id}`}
                className="animate-fade-in px-5 pb-5 text-sm leading-relaxed text-muted-foreground sm:px-6 sm:pb-6"
              >
                {faq.answer}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
