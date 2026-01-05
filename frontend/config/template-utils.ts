/**
 * Template utility functions for frontend template management
 */

import { TEMPLATE_CATEGORIES, APPROVAL_STATUS } from '@/config/constants';

export interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  body_html: string;
  body_text?: string;
  category: string;
  is_global: boolean;
  is_draft: boolean;
  is_published: boolean;
  approval_status: 'draft' | 'pending' | 'approved' | 'rejected';
  version: number;
  version_notes?: string;
  source_template_id?: string;
  source_template_name?: string;
  source_template_version?: number;
  has_newer_version?: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
  organization?: {
    id: string;
    name: string;
  };
}

/**
 * Get category display information by category value
 */
export function getCategoryInfo(category: string) {
  return TEMPLATE_CATEGORIES.find(c => c.value === category) || TEMPLATE_CATEGORIES[TEMPLATE_CATEGORIES.length - 1];
}

/**
 * Get approval status display information
 */
export function getApprovalStatusInfo(status: string) {
  const statusKey = status.toUpperCase() as keyof typeof APPROVAL_STATUS;
  return APPROVAL_STATUS[statusKey] || APPROVAL_STATUS.DRAFT;
}

/**
 * Format template version display
 */
export function formatVersion(version: number): string {
  return `v${version}`;
}

/**
 * Check if template needs update
 */
export function needsUpdate(template: EmailTemplate): boolean {
  return template.has_newer_version === true;
}

/**
 * Check if template can be edited
 */
export function canEditTemplate(template: EmailTemplate, isAdmin: boolean, isPlatformAdmin: boolean): boolean {
  // Platform admins can edit anything
  if (isPlatformAdmin) return true;
  
  // Can't edit global templates if not platform admin
  if (template.is_global) return false;
  
  // For org templates, must be admin
  return isAdmin;
}

/**
 * Check if template can be deleted
 */
export function canDeleteTemplate(template: EmailTemplate, isAdmin: boolean, isPlatformAdmin: boolean): boolean {
  // Platform admins can delete anything
  if (isPlatformAdmin) return true;
  
  // Can't delete global templates if not platform admin
  if (template.is_global) return false;
  
  // Can't delete if it has usage
  if (template.usage_count > 0) return false;
  
  // For org templates, must be admin
  return isAdmin;
}

/**
 * Check if template can be duplicated
 */
export function canDuplicateTemplate(template: EmailTemplate): boolean {
  // Can duplicate approved global templates
  if (template.is_global) {
    return template.approval_status === 'approved';
  }
  
  // Can duplicate published org templates
  return template.is_published;
}

/**
 * Generate preview text from HTML body
 */
export function generatePreviewText(htmlBody: string, maxLength: number = 150): string {
  // Remove HTML tags
  const text = htmlBody.replace(/<[^>]*>/g, '');
  
  // Remove extra whitespace
  const cleaned = text.replace(/\s+/g, ' ').trim();
  
  // Truncate if needed
  if (cleaned.length <= maxLength) {
    return cleaned;
  }
  
  return cleaned.substring(0, maxLength) + '...';
}

/**
 * Extract variables from template body
 */
export function extractVariables(body: string): string[] {
  const variableRegex = /\{\{\s*(\w+)\s*\}\}/g;
  const variables = new Set<string>();
  
  let match;
  while ((match = variableRegex.exec(body)) !== null) {
    variables.add(match[1]);
  }
  
  return Array.from(variables);
}

/**
 * Validate template body for required variables
 */
export function validateTemplateVariables(body: string, requiredVars: string[]): {
  isValid: boolean;
  missingVars: string[];
} {
  const presentVars = extractVariables(body);
  const missingVars = requiredVars.filter(v => !presentVars.includes(v));
  
  return {
    isValid: missingVars.length === 0,
    missingVars
  };
}

/**
 * Format date for display
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) {
    return 'Today';
  } else if (diffDays === 1) {
    return 'Yesterday';
  } else if (diffDays < 7) {
    return `${diffDays} days ago`;
  } else {
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  }
}

/**
 * Format relative time
 */
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffMins < 1) {
    return 'Just now';
  } else if (diffMins < 60) {
    return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
  } else if (diffHours < 24) {
    return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  } else if (diffDays < 30) {
    return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
  } else {
    return formatDate(dateString);
  }
}

/**
 * Get badge color for template status
 */
export function getTemplateBadgeColor(template: EmailTemplate): string {
  if (template.is_global) {
    return 'bg-blue-100 text-blue-800';
  } else if (template.is_draft) {
    return 'bg-gray-100 text-gray-800';
  } else if (template.is_published) {
    return 'bg-green-100 text-green-800';
  }
  return 'bg-gray-100 text-gray-800';
}

/**
 * Get status label for template
 */
export function getTemplateStatusLabel(template: EmailTemplate): string {
  if (template.is_global) {
    return 'Global';
  } else if (template.is_draft) {
    return 'Draft';
  } else if (template.is_published) {
    return 'Published';
  }
  return 'Unknown';
}

/**
 * Sort templates by various criteria
 */
export function sortTemplates<T extends EmailTemplate>(
  templates: T[],
  sortBy: 'name' | 'updated' | 'usage' | 'version',
  order: 'asc' | 'desc' = 'asc'
): T[] {
  const sorted = [...templates].sort((a, b) => {
    let compareValue = 0;
    
    switch (sortBy) {
      case 'name':
        compareValue = a.name.localeCompare(b.name);
        break;
      case 'updated':
        compareValue = new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime();
        break;
      case 'usage':
        compareValue = a.usage_count - b.usage_count;
        break;
      case 'version':
        compareValue = a.version - b.version;
        break;
    }
    
    return order === 'asc' ? compareValue : -compareValue;
  });
  
  return sorted;
}

/**
 * Filter templates by search query
 */
export function filterTemplatesBySearch<T extends EmailTemplate>(
  templates: T[],
  searchQuery: string
): T[] {
  if (!searchQuery.trim()) return templates;
  
  const query = searchQuery.toLowerCase();
  
  return templates.filter(template =>
    template.name.toLowerCase().includes(query) ||
    template.subject.toLowerCase().includes(query) ||
    template.category.toLowerCase().includes(query) ||
    (template.organization?.name && template.organization.name.toLowerCase().includes(query))
  );
}
