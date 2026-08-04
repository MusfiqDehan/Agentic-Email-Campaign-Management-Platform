/**
 * Single source of truth for the public documentation outline.
 * Both the sidebar navigation and the page content are driven from this list,
 * so a section can never appear in one place and not the other.
 */
export interface DocSection {
  id: string;
  title: string;
  /** Short label used in the sidebar when the full title is too long. */
  navLabel?: string;
  group: string;
}

export const DOC_SECTIONS: DocSection[] = [
  { id: 'overview', title: 'What is EmailCampaign?', navLabel: 'Overview', group: 'Getting started' },
  { id: 'quick-start', title: 'Quick start', group: 'Getting started' },
  { id: 'account', title: 'Create your account and organization', navLabel: 'Account & organization', group: 'Getting started' },

  { id: 'providers', title: 'Connect an email provider', navLabel: 'Email providers', group: 'Sending setup' },
  { id: 'domains', title: 'Set up a custom sending domain', navLabel: 'Custom domains', group: 'Sending setup' },
  { id: 'sender-emails', title: 'Create sender email addresses', navLabel: 'Sender emails', group: 'Sending setup' },

  { id: 'contacts', title: 'Contacts and lists', navLabel: 'Contacts & lists', group: 'Build your campaign' },
  { id: 'templates', title: 'Templates and AI content', navLabel: 'Templates & AI', group: 'Build your campaign' },
  { id: 'variables', title: 'Personalization variables', navLabel: 'Variables', group: 'Build your campaign' },
  { id: 'campaigns', title: 'Build and launch a campaign', navLabel: 'Launch a campaign', group: 'Build your campaign' },

  { id: 'analytics', title: 'Delivery logs and analytics', navLabel: 'Logs & analytics', group: 'After you send' },
  { id: 'inbox', title: 'Inbox and replies', navLabel: 'Inbox', group: 'After you send' },
  { id: 'unsubscribes', title: 'Unsubscribes and compliance', navLabel: 'Unsubscribes', group: 'After you send' },
  { id: 'notifications', title: 'Notifications', group: 'After you send' },

  { id: 'team', title: 'Team, roles and permissions', navLabel: 'Team & roles', group: 'Administration' },
  { id: 'plans', title: 'Plans and limits', navLabel: 'Plans & limits', group: 'Administration' },
  { id: 'security', title: 'Security and data handling', navLabel: 'Security', group: 'Administration' },

  { id: 'deliverability', title: 'Deliverability best practices', navLabel: 'Deliverability', group: 'Help' },
  { id: 'troubleshooting', title: 'Troubleshooting', group: 'Help' },
  { id: 'support', title: 'Getting help', group: 'Help' },
];

export const DOC_GROUPS = DOC_SECTIONS.reduce<{ group: string; sections: DocSection[] }[]>(
  (groups, section) => {
    const existing = groups.find((g) => g.group === section.group);
    if (existing) {
      existing.sections.push(section);
    } else {
      groups.push({ group: section.group, sections: [section] });
    }
    return groups;
  },
  []
);
