import {
  AtSign,
  Building2,
  CheckSquare,
  FileText,
  Globe,
  Inbox,
  LayoutDashboard,
  Package,
  ScrollText,
  Send,
  Shield,
  Users,
  UsersRound,
  type LucideIcon,
} from 'lucide-react';

export type NavItem = {
  title: string;
  href: string;
  icon: LucideIcon;
  color: string;
  shortTitle?: string;
};

export const sidebarItems: NavItem[] = [
  {
    title: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
    color: 'text-purple-600 dark:text-purple-400',
    shortTitle: 'Home',
  },
  {
    title: 'Inbox',
    href: '/dashboard/inbox',
    icon: Inbox,
    color: 'text-sky-500',
  },
  {
    title: 'Campaigns',
    href: '/dashboard/campaigns',
    icon: Send,
    color: 'text-green-500',
  },
  {
    title: 'Contacts',
    href: '/dashboard/contacts',
    icon: Users,
    color: 'text-purple-500',
  },
  {
    title: 'Templates',
    href: '/dashboard/templates',
    icon: FileText,
    color: 'text-orange-500',
  },
  {
    title: 'Delivery Logs',
    href: '/dashboard/logs',
    icon: ScrollText,
    color: 'text-cyan-500',
    shortTitle: 'Logs',
  },
  {
    title: 'Domains',
    href: '/dashboard/domains',
    icon: Globe,
    color: 'text-emerald-500',
  },
  {
    title: 'Sender Emails',
    href: '/dashboard/sender-emails',
    icon: AtSign,
    color: 'text-pink-500',
    shortTitle: 'Senders',
  },
];

export const platformAdminItems: NavItem[] = [
  {
    title: 'Admin Panel',
    href: '/dashboard/admin',
    icon: Shield,
    color: 'text-purple-600',
    shortTitle: 'Admin',
  },
  {
    title: 'Organizations',
    href: '/dashboard/admin/organizations',
    icon: Building2,
    color: 'text-indigo-500',
    shortTitle: 'Orgs',
  },
  {
    title: 'Global Templates',
    href: '/dashboard/admin/templates',
    icon: FileText,
    color: 'text-cyan-500',
  },
  {
    title: 'Pending Approvals',
    href: '/dashboard/admin/approvals',
    icon: CheckSquare,
    color: 'text-amber-500',
    shortTitle: 'Approvals',
  },
  {
    title: 'Packages',
    href: '/dashboard/admin/packages',
    icon: Package,
    color: 'text-violet-500',
  },
  {
    title: 'All Domains',
    href: '/dashboard/admin/domains',
    icon: Globe,
    color: 'text-emerald-500',
  },
];

export const orgAdminItems: NavItem[] = [
  {
    title: 'Team Insights',
    href: '/dashboard/team',
    icon: UsersRound,
    color: 'text-teal-500',
    shortTitle: 'Team',
  },
];

export const mobilePrimaryHrefs = [
  '/dashboard',
  '/dashboard/inbox',
  '/dashboard/campaigns',
  '/dashboard/contacts',
] as const;

export function isNavItemActive(pathname: string, href: string) {
  if (href === '/dashboard') {
    return pathname === '/dashboard';
  }
  if (href === '/dashboard/admin') {
    return pathname === '/dashboard/admin';
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}
