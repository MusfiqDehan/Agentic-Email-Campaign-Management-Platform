import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Sign In — EmailCampaign',
  description: 'Sign in to your EmailCampaign dashboard to manage organizations, email campaigns, contacts, and delivery analytics.',
  alternates: {
    canonical: '/login',
  },
  openGraph: {
    title: 'Sign In — EmailCampaign',
    description: 'Sign in to your EmailCampaign organization dashboard.',
    url: '/login',
    type: 'website',
    images: [
      {
        url: '/social-cover.png',
        width: 1200,
        height: 630,
        alt: 'EmailCampaign Sign In',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Sign In — EmailCampaign',
    description: 'Sign in to your EmailCampaign organization dashboard.',
    images: ['/social-cover.png'],
  },
};

export default function LoginLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
