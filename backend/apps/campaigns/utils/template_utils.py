"""
Utility functions for email template management.
"""
import re
from typing import Dict, Any, Optional
from django.db import models
from django.utils import timezone


def generate_unique_template_name(organization_id: str, base_name: str) -> str:
    """
    Generate a unique template name by appending a counter to avoid conflicts.
    
    Examples:
        "Newsletter Template" -> "Newsletter Template (Copy 1)"
        If "Newsletter Template (Copy 1)" exists -> "Newsletter Template (Copy 2)"
    
    Args:
        organization_id: Organization ID to check for uniqueness
        base_name: Base template name to start from
    
    Returns:
        str: Unique template name with counter suffix
    """
    from apps.campaigns.models import EmailTemplate
    
    # Pattern to match existing copies: "Base Name (Copy N)"
    pattern = re.compile(rf'^{re.escape(base_name)} \(Copy (\d+)\)$')
    
    # Find all templates matching the pattern
    existing_templates = EmailTemplate.objects.filter(
        organization_id=organization_id,
        is_deleted=False
    ).values_list('template_name', flat=True)
    
    # Extract copy numbers
    copy_numbers = []
    for template_name in existing_templates:
        match = pattern.match(template_name)
        if match:
            copy_numbers.append(int(match.group(1)))
    
    # Find the highest copy number and increment
    next_number = max(copy_numbers, default=0) + 1
    
    return f"{base_name} (Copy {next_number})"


def calculate_template_diff(old_template, new_template) -> Dict[str, Any]:
    """
    Calculate the differences between two template versions.
    
    Args:
        old_template: Previous version of the template
        new_template: New version of the template
    
    Returns:
        dict: Dictionary containing changed fields and their old/new values
    """
    fields_to_compare = [
        'template_name',
        'category', 
        'email_subject',
        'preview_text',
        'email_body',
        'text_body',
        'description',
        'tags',
    ]
    
    changes = {}
    
    for field in fields_to_compare:
        old_value = getattr(old_template, field, None)
        new_value = getattr(new_template, field, None)
        
        if old_value != new_value:
            changes[field] = {
                'old': old_value,
                'new': new_value,
                'changed': True
            }
    
    return {
        'changes': changes,
        'total_changes': len(changes),
        'fields_changed': list(changes.keys()),
        'timestamp': timezone.now().isoformat(),
    }


def validate_approval_transition(
    current_status: str, 
    new_status: str, 
    user
) -> tuple[bool, Optional[str]]:
    """
    Validate if a template approval status transition is allowed.
    
    Args:
        current_status: Current approval status
        new_status: Desired new status
        user: User attempting the transition
    
    Returns:
        tuple: (is_valid, error_message)
    """
    from apps.campaigns.models.email_config_models import EmailTemplate
    
    # Platform admins can perform any transition
    if user.is_platform_admin:
        return True, None
    
    # Non-admins can only create drafts or submit for approval
    allowed_transitions = {
        EmailTemplate.ApprovalStatus.DRAFT: [
            EmailTemplate.ApprovalStatus.PENDING_APPROVAL
        ],
        EmailTemplate.ApprovalStatus.REJECTED: [
            EmailTemplate.ApprovalStatus.DRAFT,
            EmailTemplate.ApprovalStatus.PENDING_APPROVAL
        ],
    }
    
    if current_status not in allowed_transitions:
        return False, f"Cannot transition from {current_status} without admin privileges"
    
    if new_status not in allowed_transitions[current_status]:
        return False, f"Transition from {current_status} to {new_status} is not allowed"
    
    return True, None


def get_template_version_chain(template) -> list:
    """
    Get the full version history chain for a template.
    
    Args:
        template: EmailTemplate instance
    
    Returns:
        list: List of template versions ordered from newest to oldest
    """
    versions = [template]
    current = template
    
    # Traverse backwards through parent versions
    while current.parent_version:
        current = current.parent_version
        versions.append(current)
    
    return versions


def format_version_notes(version_notes: str, version: int) -> str:
    """
    Format version notes with version number prefix.
    
    Args:
        version_notes: Raw version notes
        version: Version number
    
    Returns:
        str: Formatted version notes
    """
    if not version_notes:
        return f"Version {version}"
    
    return f"Version {version}: {version_notes}"


def can_edit_template(template, user) -> tuple[bool, Optional[str]]:
    """
    Check if a user can edit a specific template.
    
    Args:
        template: EmailTemplate instance
        user: User attempting to edit
    
    Returns:
        tuple: (can_edit, reason)
    """
    # Platform admins can edit anything
    if user.is_platform_admin:
        return True, None
    
    # Global templates can only be edited by platform admins
    if template.is_global:
        return False, "Only platform admins can edit global templates"
    
    # Check if user belongs to the template's organization
    if not user.organization_id:
        return False, "User must belong to an organization"
    
    if str(template.organization_id) != str(user.organization_id):
        return False, "Can only edit templates from your organization"
    
    return True, None


def can_delete_template(template, user, force: bool = False) -> tuple[bool, Optional[str]]:
    """
    Check if a user can delete a specific template.
    
    Args:
        template: EmailTemplate instance
        user: User attempting to delete
        force: Whether to force delete even with dependencies
    
    Returns:
        tuple: (can_delete, reason)
    """
    # Check edit permissions first
    can_edit, reason = can_edit_template(template, user)
    if not can_edit:
        return False, reason
    
    # Global templates with usage can't be deleted unless forced by admin
    if template.is_global and template.usage_count > 0:
        if not force or not user.is_platform_admin:
            return False, f"Global template has been used {template.usage_count} times. Cannot delete."
    
    return True, None


def get_templates_needing_updates(organization_id: str) -> list:
    """
    Get all organization templates that have newer global versions available.
    
    Args:
        organization_id: Organization ID
    
    Returns:
        list: List of dicts with template info and available update
    """
    from apps.campaigns.models import EmailTemplate
    
    # Get all organization templates that were duplicated from global templates
    org_templates = EmailTemplate.objects.filter(
        organization_id=organization_id,
        is_deleted=False,
        is_global=False,
        source_template__isnull=False
    ).select_related('source_template')
    
    templates_with_updates = []
    
    for template in org_templates:
        if template.source_template:
            # Check if the source global template has a newer version
            latest_version = EmailTemplate.objects.filter(
                id=template.source_template.id,
                is_global=True,
                approval_status=EmailTemplate.ApprovalStatus.APPROVED,
                is_deleted=False
            ).first()
            
            if latest_version and latest_version.version > template.version:
                templates_with_updates.append({
                    'template': template,
                    'current_version': template.version,
                    'latest_version': latest_version.version,
                    'version_difference': latest_version.version - template.version,
                    'global_template': latest_version,
                })
    
    return templates_with_updates
