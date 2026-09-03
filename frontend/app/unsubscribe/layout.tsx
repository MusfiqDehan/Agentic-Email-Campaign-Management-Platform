import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Email Preferences & Unsubscribe — EmailCampaign',
  description: 'Manage your email subscription preferences or unsubscribe from future marketing campaigns.',
  robots: {
    index: false,
    follow: false,
  },
};

export default function UnsubscribeLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
