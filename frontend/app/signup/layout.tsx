import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Create Account — EmailCampaign',
  description: 'Create your organization account on EmailCampaign. Start sending high-deliverability email campaigns with AI precision.',
  alternates: {
    canonical: '/signup',
  },
  openGraph: {
    title: 'Create Account — EmailCampaign',
    description: 'Get started with EmailCampaign. Free tier includes 500 emails/month, SMTP support, and real-time deliverability.',
    url: '/signup',
    type: 'website',
    images: [
      {
        url: '/social-cover.png',
        width: 1200,
        height: 630,
        alt: 'Create Account — EmailCampaign',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Create Account — EmailCampaign',
    description: 'Get started with EmailCampaign. Free tier includes 500 emails/month, SMTP support, and real-time deliverability.',
    images: ['/social-cover.png'],
  },
};

export default function SignupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
