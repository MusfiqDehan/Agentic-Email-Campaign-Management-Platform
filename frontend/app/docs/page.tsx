import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowRight, BookOpen, Rocket } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { BrandLogo } from '@/components/brand-logo';
import { SiteNav } from '@/components/landing/site-nav';
import { DocsMobileNav, DocsSidebar } from '@/components/docs/docs-nav';
import {
  Bullet,
  Bullets,
  Callout,
  Code,
  DataTable,
  Prose,
  row,
  Section,
  StatusPill,
  Step,
  Steps,
  SubHeading,
} from '@/components/docs/docs-ui';

export const metadata: Metadata = {
  title: 'Documentation — EmailCampaign',
  description:
    'Everything your organization needs to self-onboard on EmailCampaign: connect a provider, verify a custom sending domain, create sender addresses, import contacts, build templates and launch tracked campaigns.',
  keywords: [
    'email campaign documentation',
    'self onboarding',
    'custom sending domain',
    'DKIM SPF DMARC setup',
    'email marketing guide',
    'AWS SES setup guide',
    'email deliverability checklist',
  ],
  alternates: {
    canonical: '/docs',
  },
  openGraph: {
    title: 'Documentation — EmailCampaign',
    description:
      'Self-onboarding guide for organizations: providers, custom domains, sender emails, contacts, templates, campaigns and analytics.',
    url: '/docs',
    type: 'article',
    images: [
      {
        url: '/social-cover.png',
        width: 1200,
        height: 630,
        alt: 'EmailCampaign Documentation & Self-Onboarding Guide',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Documentation — EmailCampaign',
    description:
      'Self-onboarding guide for organizations: providers, custom domains, sender emails, contacts, templates, campaigns and analytics.',
    images: ['/social-cover.png'],
  },
};

export default function DocsPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background pb-[calc(4.25rem+env(safe-area-inset-bottom,0px))] lg:pb-0">
      <SiteNav variant="docs" />

      {/* Hero */}
      <section className="relative isolate overflow-hidden border-b border-border py-14 sm:py-20">
        <div className="absolute inset-0 -z-10">
          <div className="absolute left-1/2 top-0 h-[420px] w-[420px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/10 blur-[120px]" />
        </div>
        <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
            <BookOpen className="h-3.5 w-3.5 text-primary" />
            Product documentation
          </div>
          <h1 className="mt-4 max-w-3xl text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            Everything you need to <span className="gradient-text">onboard and launch</span>
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-relaxed text-muted-foreground sm:text-lg">
            A complete, self-service guide for organizations. Sign up, connect a sending provider,
            verify your own domain, build your audience, and launch tracked campaigns — no support
            ticket required.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link href="#quick-start">
              <Button className="gradient-bg border-0 text-white shadow-lg shadow-primary/25">
                <Rocket className="mr-2 h-4 w-4" />
                Start the quick start
              </Button>
            </Link>
            <Link href="#domains">
              <Button variant="outline">Set up a custom domain</Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Body */}
      <main id="main-content" tabIndex={-1} className="flex-1 outline-none">
        <div className="container mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:flex lg:gap-12 lg:px-8 lg:py-16">
          <DocsSidebar />

          <div className="min-w-0 flex-1">
            <DocsMobileNav />

            <article className="max-w-3xl space-y-12">
              {/* ------------------------------------------------------------------ */}
              <Section
                id="overview"
                title="What is EmailCampaign?"
                lead="EmailCampaign is a multi-tenant email marketing platform. Each organization gets its own isolated workspace with its own contacts, templates, sending domains, campaigns and analytics."
              >
                <Prose>
                  Everything you do lives inside your organization. Members you invite see your data
                  and nothing from any other tenant. Within that workspace you can:
                </Prose>
                <Bullets>
                  <Bullet>
                    <strong className="text-foreground">Send through your own provider</strong> —
                    Gmail or Outlook over SMTP, Amazon SES, SendGrid or Brevo. The platform builds
                    the right sending backend from whichever credentials you store.
                  </Bullet>
                  <Bullet>
                    <strong className="text-foreground">Use your own domain</strong> — register a
                    sending domain, publish the DNS records we generate, and send as{' '}
                    <Code>anything@yourcompany.com</Code>.
                  </Bullet>
                  <Bullet>
                    <strong className="text-foreground">Build reusable templates</strong> — write
                    HTML yourself or generate a first draft with the built-in AI assistant, then
                    personalize with contact variables.
                  </Bullet>
                  <Bullet>
                    <strong className="text-foreground">Launch and track campaigns</strong> — target
                    contact lists, track opens and clicks, and watch delivery, bounce and complaint
                    rates update in real time.
                  </Bullet>
                </Bullets>
                <Callout variant="note" title="Who this guide is for">
                  Organization owners and admins doing first-time setup, and team members who need
                  to run day-to-day campaigns. Sections are ordered the way you will actually work
                  through them.
                </Callout>
              </Section>

              {/* ------------------------------------------------------------------ */}
              <Section
                id="quick-start"
                title="Quick start"
                lead="The shortest path from a new account to a sent campaign. Each step links to the section with the full detail."
              >
                <Steps>
                  <Step n={1} title="Create your account and organization">
                    Sign up, confirm your email, and log in. Your organization is created for you
                    during signup. See <DocLink href="#account">Account &amp; organization</DocLink>.
                  </Step>
                  <Step n={2} title="Connect an email provider">
                    Add SMTP credentials (Gmail, Outlook, or any SMTP host) or an Amazon SES,
                    SendGrid or Brevo key under <strong>Settings → Email Providers</strong>. See{' '}
                    <DocLink href="#providers">Email providers</DocLink>.
                  </Step>
                  <Step n={3} title="Optional — verify a custom sending domain">
                    Add your domain, publish the DKIM, SPF and DMARC records we generate, then hit
                    Verify. See <DocLink href="#domains">Custom domains</DocLink>.
                  </Step>
                  <Step n={4} title="Import your contacts">
                    Upload a CSV or Excel file, or add contacts one at a time, and organize them
                    into lists. See <DocLink href="#contacts">Contacts &amp; lists</DocLink>.
                  </Step>
                  <Step n={5} title="Create a template">
                    Write your HTML or generate a draft with AI, and drop in personalization
                    variables. See <DocLink href="#templates">Templates &amp; AI</DocLink>.
                  </Step>
                  <Step n={6} title="Build and send your campaign">
                    Walk the campaign wizard, choose your audience and provider, turn on tracking,
                    and send. See <DocLink href="#campaigns">Launch a campaign</DocLink>.
                  </Step>
                  <Step n={7} title="Watch the results">
                    Open <strong>Delivery Logs</strong> for delivery, open, click, bounce and
                    complaint rates. See <DocLink href="#analytics">Logs &amp; analytics</DocLink>.
                  </Step>
                </Steps>
                <Callout variant="tip" title="You can send before you own a domain">
                  Steps 3 is optional. With just SMTP credentials from a mailbox you already own you
                  can send your first campaign immediately — a custom domain improves deliverability
                  and branding, but it is not a prerequisite.
                </Callout>
              </Section>

              {/* ------------------------------------------------------------------ */}
              <Section
                id="account"
                title="Create your account and organization"
                lead="Signing up creates both your user account and your organization in one step. Whoever signs up becomes the organization owner."
              >
                <SubHeading>Sign up</SubHeading>
                <Steps>
                  <Step n={1} title="Go to the signup page">
                    Open <DocLink href="/signup">Get Started</DocLink> and fill in your first and
                    last name, your organization name, a username, your email address and a
                    password.
                  </Step>
                  <Step n={2} title="Verify your email address">
                    We send a verification link to the address you entered. Click it to activate the
                    account. If it does not arrive within a few minutes, check spam and promotions
                    folders.
                  </Step>
                  <Step n={3} title="Log in">
                    Sign in at <DocLink href="/login">Log in</DocLink> and you land on your
                    dashboard. Forgot your password later? Use the reset link on the login page.
                  </Step>
                </Steps>

                <SubHeading>What the organization name is used for</SubHeading>
                <Prose>
                  Your organization name is the tenant boundary for every resource — contacts,
                  templates, campaigns, domains and logs are all scoped to it. It is also available
                  in templates as the <Code>{'{{organization_name}}'}</Code> variable, so it can
                  appear in email footers and signatures.
                </Prose>

                <Callout variant="note" title="One email, multiple organizations">
                  The same email address can belong to more than one organization. Each membership
                  is a separate account record with its own role, so joining a second organization
                  does not affect the first.
                </Callout>

                <SubHeading>Manage your profile and password</SubHeading>
                <Prose>
                  Update your name and details under <strong>Profile</strong>. Change your password
                  under <strong>Settings</strong> — you will be asked for your current password
                  before setting a new one.
                </Prose>
              </Section>

              {/* ------------------------------------------------------------------ */}
              <Section
                id="providers"
                title="Connect an email provider"
                lead="A provider is the service that physically delivers your mail. You need at least one before you can send. Add them under Settings → Email Providers → Add Provider."
              >
                <Prose>
                  Give the provider a recognizable name (for example &ldquo;Corporate Gmail&rdquo;),
                  pick the type, and enter a <strong>From Email</strong> — the address recipients
                  see in the From header. Then fill in the type-specific fields below.
                </Prose>

                <SubHeading>SMTP (Gmail, Outlook, or any SMTP host)</SubHeading>
                <DataTable
                  headers={['Field', 'What to enter']}
                  rows={[
                    row('SMTP Host', <>The server hostname, e.g. <Code>smtp.gmail.com</Code> or <Code>smtp.office365.com</Code>.</>),
                    row('Port', <>Usually <Code>587</Code> with TLS, or <Code>465</Code> with SSL.</>),
                    row('Username', 'Normally the full mailbox address.'),
                    row('Password', 'An app password, not your everyday account password (see below).'),
                    row('Use TLS / Use SSL', 'Enable TLS for port 587, SSL for port 465. Do not enable both.'),
                  ]}
                />
                <Callout variant="warning" title="Gmail and Outlook need an app password">
                  Both providers block plain account passwords over SMTP. Turn on two-factor
                  authentication in your Google or Microsoft account, generate a dedicated app
                  password, and paste that here. If you get an authentication error on save, this is
                  almost always the cause.
                </Callout>

                <SubHeading>Amazon SES</SubHeading>
                <DataTable
                  headers={['Field', 'What to enter']}
                  rows={[
                    row('Access Key ID', 'IAM access key with SES send permissions.'),
                    row('Secret Access Key', 'The matching secret for that key.'),
                    row('Session Token', 'Only needed if you use temporary STS credentials. Leave blank otherwise.'),
                    row('Region', <>The SES region your identities live in, e.g. <Code>us-east-1</Code>.</>),
                    row('Configuration Set', 'Optional. Set this to receive open, click, bounce and complaint events back from SES.'),
                  ]}
                />
                <Callout variant="tip" title="Leaving the SES sandbox">
                  A brand-new SES account is sandboxed: you can only send to addresses you have
                  verified, with a low daily cap. Request production access in the AWS console
                  before running a real campaign.
                </Callout>

                <SubHeading>SendGrid and Brevo</SubHeading>
                <Prose>
                  Both need only an <strong>API Key</strong> generated in that provider&apos;s
                  dashboard with mail-send permission.
                </Prose>

                <SubHeading>Default provider and health checks</SubHeading>
                <Bullets>
                  <Bullet>
                    <strong className="text-foreground">Set as default provider</strong> — the
                    provider pre-selected when you build a campaign. You can still override it per
                    campaign.
                  </Bullet>
                  <Bullet>
                    <strong className="text-foreground">Run health check on save</strong> — verifies
                    the credentials actually connect before you rely on them. Keep this on; a
                    provider that fails its health check will fail mid-campaign otherwise.
                  </Bullet>
                </Bullets>
                <Callout variant="security" title="Your credentials are encrypted at rest">
                  SMTP passwords, AWS keys and API keys are encrypted before they are stored and are
                  never returned in full through the API or shown again in the dashboard. To change
                  a secret, re-enter it.
                </Callout>
              </Section>

              {/* ------------------------------------------------------------------ */}
              <Section
                id="domains"
                title="Set up a custom sending domain"
                lead="Sending from your own domain — rather than a shared or personal mailbox — is the single biggest improvement you can make to deliverability and brand trust. Manage domains under Dashboard → Domains."
              >
                <SubHeading>Step 1 — Register the domain</SubHeading>
                <Prose>
                  Click <strong>Add Domain</strong>, enter the domain you want to send from (for
                  example <Code>yourcompany.com</Code>), and choose an ownership mode:
                </Prose>
                <DataTable
                  headers={['Ownership mode', 'What it means', 'When to choose it']}
                  rows={[
                    row(
                      <strong className="text-foreground">Platform-managed</strong>,
                      'The platform provisions and manages the sending identity for you in its own infrastructure.',
                      'The default. Choose this unless you specifically need to send from your own AWS account. Inbound email receiving is only available in this mode.',
                    ),
                    row(
                      <strong className="text-foreground">Organization-owned</strong>,
                      'The identity is provisioned inside your own AWS SES account, using an SES provider you already connected.',
                      'You want sending reputation, quotas and billing to sit in your AWS account. Requires an Amazon SES provider and a plan that allows organization-owned SES.',
                    ),
                  ]}
                />
                <Prose>
                  You can also change the <strong>MAIL FROM subdomain</strong> — it defaults to{' '}
                  <Code>mail</Code>, giving you a MAIL FROM domain of{' '}
                  <Code>mail.yourcompany.com</Code>. This is the domain used for bounce handling and
                  SPF alignment.
                </Prose>

                <SubHeading>Step 2 — Publish the DNS records</SubHeading>
                <Prose>
                  As soon as the domain is registered we generate the exact records to add at your
                  DNS provider (Cloudflare, Route 53, GoDaddy, Namecheap, and so on). Each row has a
                  copy button. This is what you will see:
                </Prose>
                <DataTable
                  headers={['Type', 'Name / Host', 'Purpose']}
                  rows={[
                    row(
                      <Code>CNAME</Code>,
                      <Code>&lt;token&gt;._domainkey.yourcompany.com</Code>,
                      <>
                        <strong className="text-foreground">DKIM signing — required.</strong> Three
                        of these are issued. Verification cannot complete until all three resolve.
                      </>,
                    ),
                    row(
                      <Code>MX</Code>,
                      <Code>mail.yourcompany.com</Code>,
                      'Routes bounce and complaint notifications for your custom MAIL FROM domain.',
                    ),
                    row(
                      <Code>TXT</Code>,
                      <Code>mail.yourcompany.com</Code>,
                      'SPF record authorizing the sending infrastructure for your MAIL FROM domain.',
                    ),
                    row(
                      <Code>TXT</Code>,
                      <Code>_dmarc.yourcompany.com</Code>,
                      'DMARC policy. Recommended — starts in monitoring mode so nothing is rejected.',
                    ),
                    row(
                      <Code>MX</Code>,
                      <Code>yourcompany.com</Code>,
                      'Only for platform-managed domains. Required if you want to receive replies in the built-in Inbox.',
                    ),
                  ]}
                />
                <Callout variant="warning" title="Watch out for auto-appended domains">
                  Many DNS panels automatically append your domain to the Name field. If your
                  provider does this, enter only the part before your domain — pasting the full host
                  would create <Code>...yourcompany.com.yourcompany.com</Code>. Also make sure the
                  CNAME records are <em>not</em> proxied (in Cloudflare, set them to
                  &ldquo;DNS only&rdquo;).
                </Callout>
                <Callout variant="warning" title="The root MX record replaces your existing mail routing">
                  Adding the inbound <Code>MX</Code> record on your root domain redirects mail for
                  that domain to the platform. Only add it if the domain does not already receive
                  business email elsewhere — otherwise use a dedicated subdomain such as{' '}
                  <Code>news.yourcompany.com</Code> for sending.
                </Callout>

                <SubHeading>Step 3 — Verify</SubHeading>
                <Prose>
                  DNS changes usually propagate in a few minutes but can take up to 24–48 hours.
                  Press <strong>Verify Now</strong> on the domain row to re-check on demand. The
                  status moves through these values:
                </Prose>
                <DataTable
                  headers={['Status', 'Meaning', 'What to do']}
                  rows={[
                    row(
                      <StatusPill tone="amber">PENDING_DNS</StatusPill>,
                      'The domain is registered but the records have not been detected yet.',
                      'Publish the records, then press Verify Now.',
                    ),
                    row(
                      <StatusPill tone="blue">PENDING_VERIFICATION</StatusPill>,
                      'Records found; verification is in progress.',
                      'Wait and re-check. No action needed.',
                    ),
                    row(
                      <StatusPill tone="green">VERIFIED</StatusPill>,
                      'The domain is ready to send from.',
                      'Create sender emails on it.',
                    ),
                    row(
                      <StatusPill tone="red">FAILED</StatusPill>,
                      'Verification could not complete. The error is shown on the row.',
                      'Re-check every record for typos, proxying and auto-appended domains.',
                    ),
                    row(
                      <StatusPill tone="red">SUSPENDED</StatusPill>,
                      'Sending was halted, usually for reputation or abuse reasons.',
                      'Read the suspension reason and contact support.',
                    ),
                    row(
                      <StatusPill tone="gray">DISABLED</StatusPill>,
                      'The domain was turned off for your organization.',
                      'Contact your organization admin or support.',
                    ),
                  ]}
                />
                <Callout variant="note" title="Keep the records in place">
                  Verification is not a one-time gate. If the DKIM records are later removed or
                  edited, the domain can drop out of verified status and sending from it will stop.
                </Callout>

                <SubHeading>Domain limits</SubHeading>
                <Prose>
                  How many domains you can register, and whether custom or organization-owned
                  domains are available at all, depends on your plan. The Domains page shows your
                  current usage against your limit. See{' '}
                  <DocLink href="#plans">Plans &amp; limits</DocLink>.
                </Prose>
              </Section>

              {/* ------------------------------------------------------------------ */}
              <Section
                id="sender-emails"
                title="Create sender email addresses"
                lead="Once a domain is verified, create the specific addresses you want to send from. Manage them under Dashboard → Sender Emails."
              >
                <Steps>
                  <Step n={1} title="Pick a verified domain">
                    Only domains in <StatusPill tone="green">VERIFIED</StatusPill> status can have
                    sender addresses created on them.
                  </Step>
                  <Step n={2} title="Choose the local part">
                    The part before the <Code>@</Code> — for example <Code>hello</Code>,{' '}
                    <Code>news</Code> or <Code>support</Code>, giving you{' '}
                    <Code>hello@yourcompany.com</Code>.
                  </Step>
                  <Step n={3} title="Set a display name">
                    The friendly name recipients see, such as &ldquo;Acme Newsletter&rdquo;. You can
                    edit this at any time without recreating the address.
                  </Step>
                </Steps>

                <Callout variant="tip" title="Use a real, monitored address">
                  Avoid <Code>noreply@</Code>. Mailbox providers treat addresses that never accept
                  replies less favorably, and replies from interested recipients are valuable. Pair
                  a real address with the Inbox so nothing goes unanswered.
                </Callout>

                <SubHeading>Receiving replies</SubHeading>
                <Prose>
                  Sender addresses on <strong>platform-managed</strong> domains can also receive
                  mail, and each one is marked as receiving-capable in the list. Addresses on
                  organization-owned SES domains are send-only — replies go wherever your own MX
                  records point. See <DocLink href="#inbox">Inbox</DocLink>.
                </Prose>

                <SubHeading>Suspending and deleting</SubHeading>
                <Prose>
                  Deleting a sender address stops it being selectable for new campaigns. An address
                  may also be marked <StatusPill tone="red">SUSPENDED</StatusPill> by the platform,
                  with the reason shown on the row — suspended addresses cannot send until the issue
                  is resolved. The number of sender addresses you can hold across all domains is
                  capped by your plan.
                </Prose>
              </Section>

              {/* ------------------------------------------------------------------ */}
              <Section
                id="contacts"
                title="Contacts and lists"
                lead="Contacts are the people you send to. Lists group them so campaigns can target a defined audience. Manage both under Dashboard → Contacts."
              >
                <SubHeading>Adding contacts</SubHeading>
                <Bullets>
                  <Bullet>
                    <strong className="text-foreground">One at a time</strong> — use{' '}
                    <strong>New Contact</strong> for email, name, phone and any tags.
                  </Bullet>
                  <Bullet>
                    <strong className="text-foreground">Bulk import</strong> — use{' '}
                    <strong>Import</strong> to upload a <Code>.csv</Code>, <Code>.xlsx</Code> or{' '}
                    <Code>.xls</Code> file up to 10 MB.
                  </Bullet>
                </Bullets>

                <SubHeading>Preparing your import file</SubHeading>
                <Prose>
                  Put a header row on top with one column per field. At minimum include an email
                  column; first name, last name and phone are recognized as well and feed the
                  personalization variables. During import you can:
                </Prose>
                <Bullets>
                  <Bullet>Assign every imported row to an existing contact list.</Bullet>
                  <Bullet>
                    Apply tags to the whole batch — for example <Code>imported, q1-leads</Code> —
                    which makes it easy to find or clean up that batch later.
                  </Bullet>
                </Bullets>
                <Callout variant="tip" title="Clean the file before you upload">
                  Remove duplicates, strip trailing spaces from addresses, and drop anything you are
                  not certain opted in. A list full of stale or purchased addresses generates
                  bounces and complaints that damage the sending reputation of your whole domain.
                </Callout>

                <SubHeading>Working with lists</SubHeading>
                <Prose>
                  A contact can belong to several lists at once, and the campaign wizard shows each
                  list&apos;s contact count as you select it. Structure lists around how you
                  actually segment — by product interest, lifecycle stage or region — rather than by
                  import batch.
                </Prose>

                <Callout variant="note" title="Contact limits">
                  Your plan sets a maximum number of contacts. If an import would exceed it, the
                  import is rejected — remove contacts you no longer mail, or move to a larger plan.
                </Callout>
              </Section>

              {/* ------------------------------------------------------------------ */}
              <Section
                id="templates"
                title="Templates and AI content"
                lead="Templates are reusable email designs. A campaign always sends a template, so create at least one before your first send. Manage them under Dashboard → Templates."
              >
                <SubHeading>Creating a template</SubHeading>
                <DataTable
                  headers={['Field', 'What it does']}
                  rows={[
                    row('Template Name', 'Internal label used to find it in the campaign wizard.'),
                    row('Category', 'Groups templates by purpose — newsletter, promotional, transactional, verification, and so on.'),
                    row('Email Subject', 'Default subject line. A campaign can override it.'),
                    row('Preview Text', 'The short snippet shown after the subject in most inboxes. Leaving it empty wastes prime real estate.'),
                    row('Description', 'Internal note about when to use this template. Not sent to recipients.'),
                    row('Tags', 'Free-form labels for organizing your template library.'),
                    row('Email Content', 'The HTML body, written in the built-in editor.'),
                  ]}
                />

                <SubHeading>Generating a draft with AI</SubHeading>
                <Prose>
                  Rather than starting from a blank editor, fill in the template name and subject,
                  then open the AI panel and press <strong>Generate with AI</strong>. You can steer
                  the output with:
                </Prose>
                <Bullets>
                  <Bullet>
                    <strong className="text-foreground">Tone</strong> — professional, friendly,
                    urgent, and so on.
                  </Bullet>
                  <Bullet>
                    <strong className="text-foreground">Audience</strong> — who you are writing to,
                    e.g. &ldquo;SaaS founders&rdquo;.
                  </Bullet>
                  <Bullet>
                    <strong className="text-foreground">Call to action</strong> — the action you
                    want, e.g. &ldquo;Start free trial&rdquo;.
                  </Bullet>
                </Bullets>
                <Prose>
                  The assistant fills in the body, plain-text alternative, description, tags and
                  preview text. Everything it writes is fully editable — treat it as a first draft
                  and always read it before sending.
                </Prose>

                <Callout variant="tip" title="Test what you build">
                  Send yourself a test before adding a template to a real campaign. Check it in at
                  least one desktop client and one mobile client — HTML email rendering varies far
                  more than web rendering does.
                </Callout>
              </Section>

              {/* ------------------------------------------------------------------ */}
              <Section
                id="variables"
                title="Personalization variables"
                lead="Variables let one template produce a personalized email for every recipient. Write them in double curly braces with no spaces, like {{first_name}}."
              >
                <Prose>
                  Values are substituted at send time from the contact record, the campaign and your
                  organization. These are the variables available:
                </Prose>

                <SubHeading>Contact</SubHeading>
                <DataTable
                  headers={['Variable', 'Resolves to', 'Example']}
                  rows={[
                    row(<Code>{'{{email}}'}</Code>, "The contact's email address", 'john.doe@example.com'),
                    row(<Code>{'{{first_name}}'}</Code>, 'First name', 'John'),
                    row(<Code>{'{{last_name}}'}</Code>, 'Last name', 'Doe'),
                    row(<Code>{'{{full_name}}'}</Code>, 'First and last name combined', 'John Doe'),
                    row(<Code>{'{{phone}}'}</Code>, 'Phone number', '+1234567890'),
                  ]}
                />

                <SubHeading>Campaign and organization</SubHeading>
                <DataTable
                  headers={['Variable', 'Resolves to', 'Example']}
                  rows={[
                    row(<Code>{'{{campaign_name}}'}</Code>, 'Name of the sending campaign', 'Summer Sale 2025'),
                    row(<Code>{'{{campaign_subject}}'}</Code>, 'The subject line used', "Don't miss our summer deals!"),
                    row(<Code>{'{{from_name}}'}</Code>, "Sender's display name", 'ACME Corp'),
                    row(<Code>{'{{from_email}}'}</Code>, "Sender's email address", 'hello@acme.com'),
                    row(<Code>{'{{organization_name}}'}</Code>, 'Your organization name', 'ACME Corporation'),
                  ]}
                />

                <SubHeading>System</SubHeading>
                <DataTable
                  headers={['Variable', 'Resolves to', 'Notes']}
                  rows={[
                    row(
                      <Code>{'{{unsubscribe_url}}'}</Code>,
                      'A unique one-click unsubscribe link for this recipient',
                      <strong className="text-foreground">Required for compliance. Include it in every marketing template.</strong>,
                    ),
                    row(<Code>{'{{view_in_browser_url}}'}</Code>, 'A link to view the email in a browser', 'Useful when images or CSS are blocked.'),
                    row(<Code>{'{{current_date}}'}</Code>, 'The date the email is sent', 'December 17, 2025'),
                    row(<Code>{'{{current_year}}'}</Code>, 'The current year', 'Handy for copyright footers.'),
                  ]}
                />

                <Callout variant="warning" title="Always set fallbacks">
                  If a contact has no first name, <Code>{'{{first_name}}'}</Code> would otherwise
                  render as an awkward gap — &ldquo;Hi ,&rdquo;. The campaign wizard lets you set a
                  default first name (for example &ldquo;there&rdquo;), plus a company name and
                  current year, which are used whenever the contact record is missing a value.
                </Callout>
                <Callout variant="tip" title="Spelling matters">
                  Variables are matched exactly and are case-sensitive, with no spaces inside the
                  braces. <Code>{'{{ first_name }}'}</Code> and <Code>{'{{First_Name}}'}</Code> will
                  not be substituted — they will be delivered as literal text.
                </Callout>
              </Section>

              {/* ------------------------------------------------------------------ */}
              <Section
                id="campaigns"
                title="Build and launch a campaign"
                lead="The campaign wizard walks you through details, template, audience, sending configuration and review. Start it from Dashboard → Campaigns → New Campaign."
              >
                <Steps>
                  <Step n={1} title="Campaign details">
                    Name the campaign, add optional tags and an internal description, then write the{' '}
                    <strong>Email Subject</strong> recipients will see and the{' '}
                    <strong>Preview Text</strong> that follows it in the inbox.
                  </Step>
                  <Step n={2} title="Select a template">
                    Choose from your template library. A live preview renders below the selector so
                    you can confirm you picked the right one.
                  </Step>
                  <Step n={3} title="Choose your audience">
                    Select one or more contact lists. Each card shows how many contacts it holds, so
                    you can see your total reach before committing.
                  </Step>
                  <Step n={4} title="Sending configuration and tracking">
                    Pick the provider to send through, then set your tracking options and
                    personalization fallbacks (described below).
                  </Step>
                  <Step n={5} title="Review and launch">
                    Confirm everything on the review step, then send. The campaign moves to{' '}
                    <StatusPill tone="blue">SENDING</StatusPill> and delivery is processed in the
                    background — you can leave the page.
                  </Step>
                </Steps>

                <SubHeading>Tracking options</SubHeading>
                <DataTable
                  headers={['Option', 'What it does', 'Recommendation']}
                  rows={[
                    row(
                      'Track Email Opens',
                      'Embeds an invisible pixel so opens are recorded.',
                      'On. Note that privacy features in some mail clients inflate or suppress open counts.',
                    ),
                    row(
                      'Track Link Clicks',
                      'Rewrites links so clicks are attributed to the campaign and recipient.',
                      'On. Clicks are a far more reliable engagement signal than opens.',
                    ),
                    row(
                      'Include Unsubscribe Link',
                      'Guarantees an unsubscribe link is present in the sent email.',
                      <strong className="text-foreground">Always on for marketing email.</strong>,
                    ),
                  ]}
                />

                <SubHeading>Personalization fallbacks</SubHeading>
                <Prose>
                  On the same step you can set a <strong>Company Name</strong>, a{' '}
                  <strong>Recipient First Name Placeholder</strong> used when a contact has no first
                  name, and the <strong>Current Year</strong>. These fill in the corresponding
                  template variables for this campaign.
                </Prose>

                <SubHeading>Campaign statuses</SubHeading>
                <DataTable
                  headers={['Status', 'Meaning']}
                  rows={[
                    row(<StatusPill tone="gray">DRAFT</StatusPill>, 'Saved but not sent. Fully editable.'),
                    row(<StatusPill tone="amber">SCHEDULED</StatusPill>, 'Queued to start automatically at its scheduled time.'),
                    row(<StatusPill tone="blue">SENDING</StatusPill>, 'Currently being delivered in batches.'),
                    row(<StatusPill tone="green">SENT</StatusPill>, 'Delivery has finished. Analytics keep updating as opens and clicks arrive.'),
                    row(<StatusPill tone="amber">PAUSED</StatusPill>, 'Sending was interrupted and can be resumed where it left off.'),
                    row(<StatusPill tone="red">CANCELLED</StatusPill>, 'Stopped permanently. Cannot be resumed.'),
                  ]}
                />

                <SubHeading>Pausing and resuming</SubHeading>
                <Prose>
                  A campaign that is sending can be paused from its detail page and resumed later —
                  useful if you spot a mistake mid-send. Emails already delivered cannot be recalled,
                  so pause as early as you can.
                </Prose>

                <Callout variant="tip" title="Warm up before a big send">
                  If your domain or provider is new, do not send to your entire list on day one.
                  Start with a few hundred of your most engaged contacts and increase volume over a
                  week or two. Mailbox providers judge sudden volume spikes from unknown senders
                  harshly.
                </Callout>
              </Section>

              {/* ------------------------------------------------------------------ */}
              <Section
                id="analytics"
                title="Delivery logs and analytics"
                lead="Dashboard → Delivery Logs is the record of every email your organization has sent, with rates rolled up across the top."
              >
                <DataTable
                  headers={['Metric', 'What it tells you']}
                  rows={[
                    row('Total Emails', 'How many messages were dispatched.'),
                    row('Delivered / Delivery Rate', 'Share accepted by the receiving mail server. Below roughly 95% suggests list quality problems.'),
                    row('Open Rate', 'Share of recipients who opened. Directional only — some clients pre-fetch images, others block the pixel.'),
                    row('Unique Opens', 'Distinct recipients who opened, ignoring repeat opens by the same person.'),
                    row('Click Rate', 'Share who clicked a tracked link. The most trustworthy engagement measure.'),
                    row('Bounce Rate', 'Share that could not be delivered. Keep this under about 2%.'),
                    row('Complaint Rate', 'Share who marked the message as spam. Keep this under about 0.1% — this is the metric that gets senders blocked.'),
                  ]}
                />

                <SubHeading>Per-message detail</SubHeading>
                <Prose>
                  The log table lists individual sends with their recipient, campaign and current
                  delivery status, and can be filtered while you investigate a specific problem. It
                  is the first place to look when someone reports they did not receive an email.
                </Prose>

                <Callout variant="warning" title="Act on hard bounces and complaints">
                  A hard bounce means the address does not exist — remove it, because repeatedly
                  mailing dead addresses signals to mailbox providers that your list is not
                  maintained. Never re-mail someone who filed a complaint.
                </Callout>

                <Callout variant="note" title="Where the events come from">
                  Delivery, bounce, complaint, open and click events are reported back by your
                  sending provider. If you send through Amazon SES, set a{' '}
                  <strong>Configuration Set</strong> on the provider — without it SES does not send
                  these events back and your log will show sends but little downstream detail.
                </Callout>
              </Section>

              {/* ------------------------------------------------------------------ */}
              <Section
                id="inbox"
                title="Inbox and replies"
                lead="Dashboard → Inbox collects mail sent to your sender addresses so replies to a campaign do not disappear into an unmonitored mailbox."
              >
                <Prose>
                  The Inbox shows unread count, inbox and sent totals, and the number of connected
                  accounts, with <strong>Inbox</strong>, <strong>Sent</strong> and{' '}
                  <strong>Trash</strong> folders.
                </Prose>
                <Callout variant="note" title="Requirements">
                  Receiving works for sender addresses on <strong>platform-managed</strong> domains
                  that have the inbound <Code>MX</Code> record published on the root domain. Sender
                  addresses on organization-owned SES domains are send-only. See{' '}
                  <DocLink href="#domains">Custom domains</DocLink>.
                </Callout>
              </Section>

              {/* ------------------------------------------------------------------ */}
              <Section
                id="unsubscribes"
                title="Unsubscribes and compliance"
                lead="Honoring opt-outs is both a legal requirement and the cheapest way to protect your sending reputation."
              >
                <Prose>
                  Every marketing template should contain{' '}
                  <Code>{'{{unsubscribe_url}}'}</Code>, and every campaign should have{' '}
                  <strong>Include Unsubscribe Link</strong> enabled. Each recipient receives a unique
                  link; following it opens a public unsubscribe page and immediately opts that
                  contact out of future sends — no login required on their part.
                </Prose>
                <Bullets>
                  <Bullet>Only send to people who actually opted in. Never upload purchased lists.</Bullet>
                  <Bullet>Make it obvious who is emailing and why the recipient is hearing from you.</Bullet>
                  <Bullet>Include a valid postal address in your footer where your jurisdiction requires it.</Bullet>
                  <Bullet>
                    Process opt-outs promptly — the platform does this automatically, so do not
                    re-add unsubscribed contacts through a later import.
                  </Bullet>
                </Bullets>
                <Callout variant="warning" title="Re-importing undoes your opt-outs">
                  If you import an old file that still contains people who unsubscribed, you risk
                  mailing them again. Filter your source data before every import.
                </Callout>
              </Section>

              {/* ------------------------------------------------------------------ */}
              <Section
                id="notifications"
                title="Notifications"
                lead="The platform keeps you informed about campaign progress and delivery events without you needing to refresh."
              >
                <Bullets>
                  <Bullet>
                    <strong className="text-foreground">In-app, real time</strong> — the dashboard
                    holds a live connection, so campaign progress and delivery events appear as they
                    happen. Review the history under <strong>Notifications</strong>.
                  </Bullet>
                  <Bullet>
                    <strong className="text-foreground">Browser push</strong> — opt in and your
                    browser will notify you about important events even when the dashboard tab is
                    not focused. Your browser will ask permission the first time.
                  </Bullet>
                </Bullets>
                <Callout variant="note" title="If real-time updates stop">
                  Corporate firewalls and some VPNs block the persistent connection that powers live
                  updates. The dashboard still works — figures refresh when you reload the page.
                </Callout>
              </Section>

              {/* ------------------------------------------------------------------ */}
              <Section
                id="team"
                title="Team, roles and permissions"
                lead="Organizations are multi-user. Every member works inside the same workspace, with what they can do determined by their role."
              >
                <DataTable
                  headers={['Role', 'Can do']}
                  rows={[
                    row(
                      <strong className="text-foreground">Owner</strong>,
                      'Full control of the organization, including provider credentials, domains, billing-related settings and membership.',
                    ),
                    row(
                      <strong className="text-foreground">Admin</strong>,
                      'Manage organization resources and settings — contacts, templates, campaigns, domains, sender addresses and team insights.',
                    ),
                    row(
                      <strong className="text-foreground">Member</strong>,
                      'Day-to-day campaign work within the organization, without access to administrative settings.',
                    ),
                  ]}
                />
                <SubHeading>Team Insights</SubHeading>
                <Prose>
                  Organization admins get a <strong>Team Insights</strong> view showing member
                  count, templates in use, most-used templates, notification volume and recent
                  template activity — useful for seeing which assets your team actually relies on.
                </Prose>
                <Callout variant="security" title="Least privilege">
                  Only grant owner or admin to people who genuinely need to change provider
                  credentials and domains. A mistake at that level affects every campaign your
                  organization sends.
                </Callout>
              </Section>

              {/* ------------------------------------------------------------------ */}
              <Section
                id="plans"
                title="Plans and limits"
                lead="Your organization is assigned a package that determines both hard limits and which features are switched on."
              >
                <SubHeading>Limits</SubHeading>
                <DataTable
                  headers={['Limit', 'Applies to']}
                  rows={[
                    row('Contacts', 'Total contacts you may store.'),
                    row('Campaigns per month', 'How many campaigns you may create in a calendar month.'),
                    row('Emails per day / month', 'Sending volume ceilings.'),
                    row('Emails per minute', 'Throughput throttle applied while a campaign sends.'),
                    row('Batch size', 'How many messages are dispatched per batch during a send.'),
                    row('API requests per minute', 'Rate limit on API access.'),
                    row('Max domains', 'Sending domains you may register.'),
                    row('Max sender emails', 'Sender addresses across all your domains.'),
                  ]}
                />

                <SubHeading>Feature flags</SubHeading>
                <DataTable
                  headers={['Feature', 'What it unlocks']}
                  rows={[
                    row('Custom domain', 'The ability to register and verify your own sending domains at all.'),
                    row('Organization-owned SES', 'Provisioning domains inside your own AWS SES account instead of the platform-managed one.'),
                    row('Bulk email', 'Large-audience campaign sending.'),
                    row('Advanced analytics', 'The fuller reporting surface on delivery logs.'),
                    row('A/B testing', 'Running variant tests on campaigns.'),
                    row('Priority support', 'Faster support response targets.'),
                  ]}
                />

                <Callout variant="note" title="Unlimited and per-organization exceptions">
                  A limit shown as unlimited means no cap is enforced for that dimension. Platform
                  administrators can also grant per-organization overrides on top of your package,
                  so your effective limit may be higher than the standard plan — the Domains and
                  Sender Emails pages always show your real current usage and ceiling.
                </Callout>
                <Prose>
                  Compare the standard tiers on the{' '}
                  <DocLink href="/#pricing">pricing section</DocLink> of the homepage.
                </Prose>
              </Section>

              {/* ------------------------------------------------------------------ */}
              <Section
                id="security"
                title="Security and data handling"
                lead="A short summary of how your credentials and tenant data are protected."
              >
                <Bullets>
                  <Bullet>
                    <strong className="text-foreground">Tenant isolation</strong> — every contact,
                    template, campaign, domain and log entry is scoped to your organization and is
                    not reachable by any other tenant.
                  </Bullet>
                  <Bullet>
                    <strong className="text-foreground">Encrypted credentials</strong> — SMTP
                    passwords, AWS keys and provider API keys are encrypted before storage and are
                    never returned in full through the API or displayed again in the dashboard.
                  </Bullet>
                  <Bullet>
                    <strong className="text-foreground">Authenticated sessions</strong> — access is
                    token-based, and role checks are enforced on every request rather than only in
                    the interface.
                  </Bullet>
                  <Bullet>
                    <strong className="text-foreground">Soft deletion</strong> — deleting a record
                    removes it from your workspace while preserving an audit trail, so accidental
                    deletions can be investigated.
                  </Bullet>
                </Bullets>
                <Callout variant="security" title="Rotate credentials you no longer use">
                  If a team member with provider access leaves, rotate the SMTP app password or IAM
                  key in the upstream provider and re-enter it here. Removing their platform account
                  alone does not invalidate credentials they may have copied.
                </Callout>
              </Section>

              {/* ------------------------------------------------------------------ */}
              <Section
                id="deliverability"
                title="Deliverability best practices"
                lead="Landing in the inbox is earned. These are the practices that matter most, in rough order of impact."
              >
                <Steps>
                  <Step n={1} title="Authenticate your domain">
                    Publish DKIM, SPF and DMARC as described in{' '}
                    <DocLink href="#domains">Custom domains</DocLink>. Unauthenticated mail is
                    increasingly rejected outright by major providers.
                  </Step>
                  <Step n={2} title="Send only to people who opted in">
                    Permission is the foundation. Everything else is optimization on top of it.
                  </Step>
                  <Step n={3} title="Warm up new domains and providers gradually">
                    Build volume over days or weeks rather than sending your full list on the first
                    day.
                  </Step>
                  <Step n={4} title="Keep your list clean">
                    Remove hard bounces immediately, and stop mailing contacts who have not engaged
                    in a long time. Inactive recipients drag down your engagement signals.
                  </Step>
                  <Step n={5} title="Make unsubscribing easy">
                    A visible unsubscribe link produces far fewer spam complaints than a hidden one.
                    A complaint hurts you much more than an opt-out does.
                  </Step>
                  <Step n={6} title="Write like a human">
                    Avoid all-caps subject lines, walls of exclamation marks, and image-only emails
                    with no text. Keep a sensible ratio of text to images.
                  </Step>
                  <Step n={7} title="Watch your rates every send">
                    Rising bounce or complaint rates are the earliest warning that something is
                    wrong. Investigate before the next campaign, not after.
                  </Step>
                </Steps>
              </Section>

              {/* ------------------------------------------------------------------ */}
              <Section
                id="troubleshooting"
                title="Troubleshooting"
                lead="The issues organizations hit most often during self-onboarding, and how to resolve them."
              >
                <DataTable
                  headers={['Symptom', 'Likely cause and fix']}
                  rows={[
                    row(
                      <strong className="text-foreground">Verification email never arrived</strong>,
                      'Check spam and promotions folders first. Confirm the address was typed correctly; if it was wrong, sign up again with the correct address.',
                    ),
                    row(
                      <strong className="text-foreground">Provider fails its health check</strong>,
                      'For Gmail or Outlook, you almost certainly used your account password instead of an app password. Otherwise re-check host, port and the TLS/SSL combination — port 587 uses TLS, port 465 uses SSL, never both.',
                    ),
                    row(
                      <strong className="text-foreground">Domain stuck on PENDING_DNS</strong>,
                      'The DKIM records are not resolving. Check for a domain auto-appended to the Name field by your DNS panel, and make sure the CNAMEs are not proxied. Propagation can take up to 48 hours.',
                    ),
                    row(
                      <strong className="text-foreground">Domain shows FAILED</strong>,
                      'Read the error text on the domain row, correct the record it names, then press Verify Now. A single mistyped DKIM token blocks the whole verification.',
                    ),
                    row(
                      <strong className="text-foreground">Cannot create a sender email</strong>,
                      'The domain must be VERIFIED, and you must be under your plan’s sender-email limit. Both are shown on their respective pages.',
                    ),
                    row(
                      <strong className="text-foreground">Campaign will not send</strong>,
                      'Confirm you selected a provider, at least one contact list with contacts in it, and a template. Check that the sending address is not suspended and that you have not hit a daily or monthly volume limit.',
                    ),
                    row(
                      <strong className="text-foreground">Variables appear as literal text</strong>,
                      <>
                        The variable name does not match exactly. Use{' '}
                        <Code>{'{{first_name}}'}</Code> — lowercase, underscores, no spaces inside
                        the braces.
                      </>,
                    ),
                    row(
                      <strong className="text-foreground">Emails land in spam</strong>,
                      <>
                        Usually missing domain authentication or list quality. Work through{' '}
                        <DocLink href="#deliverability">Deliverability best practices</DocLink>{' '}
                        in order.
                      </>,
                    ),
                    row(
                      <strong className="text-foreground">Opens look implausibly low or high</strong>,
                      'Open tracking is approximate. Privacy protection in some mail clients pre-loads the tracking pixel, and others block it entirely. Judge performance by clicks.',
                    ),
                    row(
                      <strong className="text-foreground">Import rejected</strong>,
                      'The file must be .csv, .xlsx or .xls and under 10 MB, and the import must not push you past your contact limit. Split very large files into batches.',
                    ),
                    row(
                      <strong className="text-foreground">SES sends succeed but no open/click data</strong>,
                      'Set a Configuration Set on the Amazon SES provider. Without it, SES does not report events back to the platform.',
                    ),
                  ]}
                />
              </Section>

              {/* ------------------------------------------------------------------ */}
              <Section
                id="support"
                title="Getting help"
                lead="If this guide did not answer your question, here is where to go next."
              >
                <Bullets>
                  <Bullet>
                    <strong className="text-foreground">Check Delivery Logs first</strong> — for
                    anything about a specific message, the per-message status in the log is the
                    fastest answer.
                  </Bullet>
                  <Bullet>
                    <strong className="text-foreground">Ask your organization admin</strong> — plan
                    limits, feature availability and role changes are set at the organization level.
                  </Bullet>
                  <Bullet>
                    <strong className="text-foreground">Contact support</strong> — for suspended
                    domains or addresses, plan changes, or anything you cannot resolve from the
                    dashboard. Include your organization name, the domain or campaign involved, and
                    what you have already tried.
                  </Bullet>
                </Bullets>

                <div className="rounded-2xl border border-border bg-gradient-to-br from-primary/10 to-purple-500/10 p-6 sm:p-8">
                  <h3 className="text-xl font-bold tracking-tight">Ready to send your first campaign?</h3>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Create your organization and work through the quick start — most teams are
                    sending within an afternoon.
                  </p>
                  <div className="mt-5 flex flex-wrap gap-3">
                    <Link href="/signup">
                      <Button className="gradient-bg border-0 text-white shadow-lg shadow-primary/25">
                        Create your organization
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </Button>
                    </Link>
                    <Link href="#quick-start">
                      <Button variant="outline">Back to quick start</Button>
                    </Link>
                  </div>
                </div>
              </Section>
            </article>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-muted/20">
        <div className="container mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 py-8 sm:flex-row sm:px-6 lg:px-8">
          <Link href="/" className="transition-transform hover:scale-105">
            <BrandLogo size={32} wordmarkClassName="text-lg" />
          </Link>
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} EmailCampaign Inc. All rights reserved.
          </p>
          <ThemeToggle />
        </div>
      </footer>
    </div>
  );
}

/** Inline link styled consistently across the docs body. */
function DocLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="font-medium text-primary underline-offset-4 hover:underline">
      {children}
    </Link>
  );
}
