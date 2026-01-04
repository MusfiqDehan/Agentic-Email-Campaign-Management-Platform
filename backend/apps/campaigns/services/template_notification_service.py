"""
Service for managing template update notifications.
"""
from typing import List, Optional
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from apps.campaigns.models import (
    EmailTemplate,
    TemplateUpdateNotification,
    OrganizationTemplateNotification,
    TemplateUsageLog,
    TemplateApprovalRequest,
)


def create_template_update_notification(
    template: EmailTemplate,
    old_version: int,
    new_version: int,
    update_summary: str
) -> TemplateUpdateNotification:
    """
    Create a notification for a global template update and notify all organizations using it.
    
    Args:
        template: The global template that was updated
        old_version: Previous version number
        new_version: New version number
        update_summary: Summary of changes made
    
    Returns:
        TemplateUpdateNotification instance
    """
    with transaction.atomic():
        # Create the main notification
        notification = TemplateUpdateNotification.objects.create(
            global_template=template,
            old_version=old_version,
            new_version=new_version,
            update_summary=update_summary,
        )
        
        # Find all organizations that have used this template
        usage_logs = TemplateUsageLog.objects.filter(
            template=template
        ).values_list('organization_id', flat=True).distinct()
        
        # Create organization-specific notifications
        org_notifications = []
        for org_id in usage_logs:
            org_notifications.append(
                OrganizationTemplateNotification(
                    notification=notification,
                    organization_id=org_id,
                )
            )
        
        OrganizationTemplateNotification.objects.bulk_create(org_notifications)
        
        # Queue email notifications (will be sent by Celery task)
        # send_template_update_emails.delay(notification.id)
        
        return notification


def create_approval_request_notification(approval_request: TemplateApprovalRequest) -> None:
    """
    Notify platform admins about a pending approval request.
    
    Args:
        approval_request: The approval request instance
    """
    from apps.authentication.models import User
    
    # Get all platform admins except the requester
    platform_admins = User.objects.filter(
        is_platform_admin=True,
        is_active=True
    ).exclude(id=approval_request.requested_by.id)
    
    template_name = approval_request.template.template_name
    requester_name = approval_request.requested_by.get_full_name() or approval_request.requested_by.username
    
    subject = f"Template Approval Request: {template_name}"
    message = f"""
    A new template approval request has been submitted.
    
    Template: {template_name}
    Version: {approval_request.version_before_approval}
    Requested by: {requester_name}
    Notes: {approval_request.approval_notes or 'No notes provided'}
    
    Please review and approve/reject this request in the admin panel.
    """
    
    admin_emails = list(platform_admins.values_list('email', flat=True))
    
    if admin_emails:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=True,
        )


def send_template_update_emails(notification_id: str) -> dict:
    """
    Send email notifications to organization admins about template updates.
    This should be called as a Celery task.
    
    Args:
        notification_id: UUID of the TemplateUpdateNotification
    
    Returns:
        dict: Summary of sent emails
    """
    try:
        notification = TemplateUpdateNotification.objects.get(id=notification_id)
    except TemplateUpdateNotification.DoesNotExist:
        return {'error': 'Notification not found', 'sent': 0}
    
    template_name = notification.global_template.template_name
    
    # Get all organization notifications
    org_notifications = OrganizationTemplateNotification.objects.filter(
        notification=notification
    ).select_related('organization')
    
    sent_count = 0
    failed_count = 0
    
    for org_notification in org_notifications:
        org = org_notification.organization
        
        # Get organization admins and owner
        from apps.authentication.models import User, OrganizationMembership
        
        admin_memberships = OrganizationMembership.objects.filter(
            organization=org,
            role__in=['owner', 'admin']
        ).select_related('user')
        
        admin_emails = [m.user.email for m in admin_memberships if m.user.email]
        
        if not admin_emails:
            continue
        
        subject = f"Update Available: {template_name} Template"
        message = f"""
        A global template you're using has been updated.
        
        Template: {template_name}
        Old Version: v{notification.old_version}
        New Version: v{notification.new_version}
        
        What changed:
        {notification.update_summary}
        
        You can update your copy of this template in the Templates section of your dashboard.
        """
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=False,
            )
            sent_count += len(admin_emails)
        except Exception as e:
            failed_count += 1
            print(f"Failed to send notification to {org.name}: {str(e)}")
    
    return {
        'sent': sent_count,
        'failed': failed_count,
        'notification_id': str(notification_id),
    }


def mark_notification_as_read(
    notification_id: str,
    organization_id: str,
    user
) -> OrganizationTemplateNotification:
    """
    Mark a template update notification as read for an organization.
    
    Args:
        notification_id: UUID of the notification
        organization_id: UUID of the organization
        user: User marking it as read
    
    Returns:
        Updated OrganizationTemplateNotification instance
    """
    org_notification = OrganizationTemplateNotification.objects.get(
        notification_id=notification_id,
        organization_id=organization_id
    )
    
    org_notification.is_read = True
    org_notification.read_at = timezone.now()
    org_notification.read_by = user
    org_notification.save()
    
    return org_notification


def mark_template_as_updated(
    notification_id: str,
    organization_id: str
) -> OrganizationTemplateNotification:
    """
    Mark that an organization has updated their template copy.
    
    Args:
        notification_id: UUID of the notification
        organization_id: UUID of the organization
    
    Returns:
        Updated OrganizationTemplateNotification instance
    """
    org_notification = OrganizationTemplateNotification.objects.get(
        notification_id=notification_id,
        organization_id=organization_id
    )
    
    org_notification.template_updated = True
    org_notification.save()
    
    return org_notification


def get_unread_notifications(organization_id: str) -> List[OrganizationTemplateNotification]:
    """
    Get all unread template update notifications for an organization.
    
    Args:
        organization_id: UUID of the organization
    
    Returns:
        QuerySet of unread notifications
    """
    return OrganizationTemplateNotification.objects.filter(
        organization_id=organization_id,
        is_read=False,
        notification__is_active=True
    ).select_related(
        'notification',
        'notification__global_template'
    ).order_by('-notification__created_at')


def get_notification_count(organization_id: str) -> dict:
    """
    Get count of notifications for an organization.
    
    Args:
        organization_id: UUID of the organization
    
    Returns:
        dict: Counts of different notification states
    """
    notifications = OrganizationTemplateNotification.objects.filter(
        organization_id=organization_id,
        notification__is_active=True
    )
    
    return {
        'total': notifications.count(),
        'unread': notifications.filter(is_read=False).count(),
        'pending_update': notifications.filter(
            is_read=True,
            template_updated=False
        ).count(),
    }
