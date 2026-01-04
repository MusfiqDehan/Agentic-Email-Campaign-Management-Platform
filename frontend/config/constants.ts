/**
 * Template and Campaign Management Constants
 */

export const TEMPLATE_CATEGORIES = [
  {
    value: 'welcome',
    label: 'Welcome',
    icon: '👋',
    color: 'bg-blue-100 text-blue-800',
    description: 'Welcome emails for new users or subscribers'
  },
  {
    value: 'newsletter',
    label: 'Newsletter',
    icon: '📧',
    color: 'bg-purple-100 text-purple-800',
    description: 'Regular newsletter communications'
  },
  {
    value: 'promotional',
    label: 'Promotional',
    icon: '🎁',
    color: 'bg-green-100 text-green-800',
    description: 'Marketing and promotional campaigns'
  },
  {
    value: 'transactional',
    label: 'Transactional',
    icon: '💳',
    color: 'bg-yellow-100 text-yellow-800',
    description: 'Transaction confirmations and receipts'
  },
  {
    value: 'follow_up',
    label: 'Follow-up',
    icon: '🔔',
    color: 'bg-orange-100 text-orange-800',
    description: 'Follow-up and reminder emails'
  },
  {
    value: 'event',
    label: 'Event',
    icon: '📅',
    color: 'bg-indigo-100 text-indigo-800',
    description: 'Event invitations and updates'
  },
  {
    value: 'announcement',
    label: 'Announcement',
    icon: '📢',
    color: 'bg-pink-100 text-pink-800',
    description: 'Important announcements and updates'
  },
  {
    value: 'other',
    label: 'Other',
    icon: '📄',
    color: 'bg-gray-100 text-gray-800',
    description: 'Miscellaneous templates'
  }
] as const;

export const APPROVAL_STATUS = {
  DRAFT: {
    value: 'draft',
    label: 'Draft',
    color: 'bg-gray-100 text-gray-800',
    icon: '📝'
  },
  PENDING: {
    value: 'pending',
    label: 'Pending Approval',
    color: 'bg-yellow-100 text-yellow-800',
    icon: '⏳'
  },
  APPROVED: {
    value: 'approved',
    label: 'Approved',
    color: 'bg-green-100 text-green-800',
    icon: '✅'
  },
  REJECTED: {
    value: 'rejected',
    label: 'Rejected',
    color: 'bg-red-100 text-red-800',
    icon: '❌'
  }
} as const;

export const TEMPLATE_TYPES = {
  GLOBAL: {
    value: 'global',
    label: 'Global Templates',
    description: 'Platform-wide templates available to all organizations'
  },
  ORGANIZATION: {
    value: 'organization',
    label: 'My Templates',
    description: 'Organization-specific templates'
  }
} as const;

export const NOTIFICATION_TYPES = {
  TEMPLATE_UPDATE: {
    value: 'template_update',
    label: 'Template Updated',
    icon: '🔄',
    color: 'bg-blue-100 text-blue-800'
  },
  APPROVAL_REQUEST: {
    value: 'approval_request',
    label: 'Approval Request',
    icon: '📋',
    color: 'bg-purple-100 text-purple-800'
  },
  APPROVAL_APPROVED: {
    value: 'approval_approved',
    label: 'Approved',
    icon: '✅',
    color: 'bg-green-100 text-green-800'
  },
  APPROVAL_REJECTED: {
    value: 'approval_rejected',
    label: 'Rejected',
    icon: '❌',
    color: 'bg-red-100 text-red-800'
  }
} as const;

export const CAMPAIGN_STATUS = {
  DRAFT: {
    value: 'draft',
    label: 'Draft',
    color: 'bg-gray-100 text-gray-800'
  },
  SCHEDULED: {
    value: 'scheduled',
    label: 'Scheduled',
    color: 'bg-blue-100 text-blue-800'
  },
  RUNNING: {
    value: 'running',
    label: 'Running',
    color: 'bg-green-100 text-green-800'
  },
  PAUSED: {
    value: 'paused',
    label: 'Paused',
    color: 'bg-yellow-100 text-yellow-800'
  },
  COMPLETED: {
    value: 'completed',
    label: 'Completed',
    color: 'bg-purple-100 text-purple-800'
  },
  CANCELLED: {
    value: 'cancelled',
    label: 'Cancelled',
    color: 'bg-red-100 text-red-800'
  }
} as const;
