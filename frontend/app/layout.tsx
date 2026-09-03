import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://emailcampaign.musfiqdehan.com";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "EmailCampaign — Modern AI-Powered Email Outreach & Marketing Platform",
    template: "%s | EmailCampaign",
  },
  description:
    "Deliver smarter emails with AI precision. Powerful multi-tenant email campaign management with automated DNS deliverability, custom sending domains, multi-provider sending, and real-time analytics.",
  applicationName: "EmailCampaign",
  keywords: [
    "email marketing",
    "cold outreach",
    "AI email copywriting",
    "email campaign management",
    "custom sending domains",
    "DKIM SPF DMARC deliverability",
    "AWS SES email marketing",
    "multi-tenant email platform",
    "inbox placement optimization",
    "real-time email analytics",
  ],
  authors: [{ name: "EmailCampaign Inc." }],
  creator: "EmailCampaign Inc.",
  publisher: "EmailCampaign Inc.",
  alternates: {
    canonical: "/",
  },
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/logo.svg", type: "image/svg+xml" },
    ],
    shortcut: "/favicon.ico",
    apple: "/logo.svg",
  },
  openGraph: {
    title: "EmailCampaign — Modern AI-Powered Email Outreach & Marketing Platform",
    description:
      "Deliver smarter emails with AI precision. Reach real inboxes with custom domains, automated DNS deliverability, AI copywriting, and real-time tracking.",
    url: siteUrl,
    siteName: "EmailCampaign",
    locale: "en_US",
    type: "website",
    images: [
      {
        url: "/social-cover.png",
        width: 1200,
        height: 630,
        alt: "EmailCampaign — AI-Powered Email Outreach & Marketing Platform",
        type: "image/png",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "EmailCampaign — Modern AI-Powered Email Outreach & Marketing Platform",
    description:
      "Deliver smarter emails with AI precision. Reach real inboxes with custom domains, automated DNS deliverability, and real-time analytics.",
    images: ["/social-cover.png"],
    creator: "@emailcampaign",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#7e22ce" },
    { media: "(prefers-color-scheme: dark)", color: "#0b1220" },
  ],
};

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "SoftwareApplication",
      "@id": `${siteUrl}/#software`,
      name: "EmailCampaign",
      applicationCategory: "BusinessApplication",
      operatingSystem: "Web",
      url: siteUrl,
      description:
        "AI-powered multi-tenant email campaign and cold outreach management platform with automated DNS verification, custom sending domains, and real-time analytics.",
      offers: [
        {
          "@type": "Offer",
          name: "Starter",
          price: "0",
          priceCurrency: "USD",
          description: "Free forever tier with up to 500 contacts and SMTP sending",
        },
        {
          "@type": "Offer",
          name: "Pro",
          price: "39",
          priceCurrency: "USD",
          description: "AWS SES and custom SMTP support with AI copywriting and up to 15,000 contacts",
        },
        {
          "@type": "Offer",
          name: "Growth",
          price: "99",
          priceCurrency: "USD",
          description: "Multi-domain DKIM/SPF management, dedicated warm-up, and 150,000+ monthly emails",
        },
      ],
      featureList: [
        "AI email copywriting and subject line generator",
        "Automated SPF, DKIM, and DMARC DNS verification",
        "Multi-provider dispatch with Amazon SES, SMTP, SendGrid, and Brevo",
        "Real-time deliverability and open/click tracking webhooks",
        "Multi-tenant organization workspaces with RBAC",
      ],
      screenshot: `${siteUrl}/social-cover.png`,
    },
    {
      "@type": "Organization",
      "@id": `${siteUrl}/#organization`,
      name: "EmailCampaign",
      url: siteUrl,
      logo: `${siteUrl}/logo.svg`,
      sameAs: [],
      contactPoint: {
        "@type": "ContactPoint",
        contactType: "customer support",
        email: "support@emailcampaign.io",
      },
    },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning data-scroll-behavior="smooth">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen bg-background`}
      >
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
