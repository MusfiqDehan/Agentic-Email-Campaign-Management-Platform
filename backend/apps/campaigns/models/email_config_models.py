"""
Email template model for storing reusable email templates.
"""
import uuid
from django.db import models
from django.conf import settings
from apps.utils.base_models import BaseModel
from apps.authentication.models import Organization


class EmailTemplate(BaseModel):
    """
    Stores email templates with dynamic variables.
    
    Supports both global templates (available to all organizations) and 
    organization-specific templates. Includes versioning and approval workflow.
    """
    
    class TemplateCategory(models.TextChoices):
        # Transactional
        EMAIL_VERIFICATION = 'EMAIL_VERIFICATION', 'Email Verification'
        PASSWORD_RESET = 'PASSWORD_RESET', 'Password Reset'
        WELCOME = 'WELCOME', 'Welcome'
        FOLLOW_UP = 'FOLLOW_UP', 'Follow-up'
        
        # Campaign
        NEWSLETTER = 'NEWSLETTER', 'Newsletter'
        PROMOTIONAL = 'PROMOTIONAL', 'Promotional'
        ANNOUNCEMENT = 'ANNOUNCEMENT', 'Announcement'
        EVENT = 'EVENT', 'Event'
        
        # User management
        INVITATION = 'INVITATION', 'Invitation'
        REMINDER = 'REMINDER', 'Reminder'
        NOTIFICATION = 'NOTIFICATION', 'Notification'
        
        # Subscription
        SUBSCRIPTION_CONFIRMATION = 'SUBSCRIPTION_CONFIRMATION', 'Subscription Confirmation'
        SUBSCRIPTION_RENEWAL = 'SUBSCRIPTION_RENEWAL', 'Subscription Renewal'
        
        # Transaction
        TRANSACTIONAL = 'TRANSACTIONAL', 'Transactional'
        
        # Other
        OTHER = 'OTHER', 'Other'
    
    class ApprovalStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PENDING_APPROVAL = 'PENDING_APPROVAL', 'Pending Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Organization ownership (nullable for global templates)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='email_templates',
        null=True,
        blank=True,
        help_text="Organization that owns this template. Null for global templates."
    )
    
    # Global template flags
    is_global = models.BooleanField(
        default=False,
        help_text="Whether this is a global template available to all organizations"
    )
    
    # Template lineage and tracking
    source_template = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='duplicates',
        help_text="The global template this was duplicated from"
    )
    usage_count = models.IntegerField(
        default=0,
        help_text="Number of times this global template has been duplicated"
    )
    duplicated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='duplicated_templates',
        help_text="User who duplicated this template from a global template"
    )
    
    # Versioning
    version = models.IntegerField(
        default=1,
        help_text="Version number of this template"
    )
    version_notes = models.TextField(
        blank=True,
        help_text="Changelog or notes about this version"
    )
    parent_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_versions',
        help_text="Previous version of this template"
    )
    
    # Draft and approval workflow
    is_draft = models.BooleanField(
        default=False,
        help_text="Whether this is a draft version not yet published"
    )
    approval_status = models.CharField(
        max_length=50,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.APPROVED,
        help_text="Approval status for global templates"
    )
    submitted_for_approval_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this template was submitted for approval"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_templates',
        help_text="Platform admin who approved this template"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this template was approved"
    )
    
    # Template identification
    template_name = models.CharField(max_length=255)
    category = models.CharField(
        max_length=100, 
        choices=TemplateCategory.choices, 
        default=TemplateCategory.OTHER,
        help_text="Template category for organization"
    )
    
    # Email content
    email_subject = models.CharField(max_length=255)
    preview_text = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Preview text shown in email clients"
    )
    email_body = models.TextField(help_text="Use {{variable_name}} for dynamic content.")
    text_body = models.TextField(blank=True, help_text="Plain text fallback content.")
    
    # Template metadata
    description = models.TextField(blank=True, help_text="Internal description of this template")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing templates")

    class Meta:
        constraints = [
            # Unique template name per organization (excluding global templates)
            models.UniqueConstraint(
                fields=['organization', 'template_name'],
                condition=models.Q(is_deleted=False, is_global=False),
                name='unique_template_per_org'
            ),
            # Global templates must not have an organization
            models.CheckConstraint(
                check=models.Q(is_global=False) | models.Q(organization__isnull=True),
                name='global_templates_no_org'
            ),
        ]
        indexes = [
            models.Index(fields=['organization', 'category']),
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['is_global', 'approval_status', 'is_draft']),
            models.Index(fields=['source_template', 'organization']),
        ]
        verbose_name = "Email Template"
        verbose_name_plural = "Email Templates"

    def __str__(self):
        if self.is_global:
            return f"{self.template_name} (Global v{self.version})"
        return f"{self.template_name} ({self.organization.name if self.organization else 'No Org'})"
    
    def render(self, context: dict) -> dict:
        """
        Render the template with the given context.
        
        Args:
            context: Dictionary of variable values
            
        Returns:
            Dict with rendered subject, html_body, text_body
        """
        subject = self.email_subject
        html_body = self.email_body
        text_body = self.text_body or ""
        preview = self.preview_text or ""
        
        # Simple variable replacement
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            str_value = str(value) if value is not None else ""
            subject = subject.replace(placeholder, str_value)
            html_body = html_body.replace(placeholder, str_value)
            text_body = text_body.replace(placeholder, str_value)
            preview = preview.replace(placeholder, str_value)
        
        return {
            'subject': subject,
            'html_body': html_body,
            'text_body': text_body,
            'preview_text': preview,
        }
    
    def get_variables(self) -> list:
        """
        Extract variable names from the template.
        
        Returns:
            List of variable names found in the template
        """
        import re
        pattern = r'\{\{(\w+)\}\}'
        
        all_text = f"{self.email_subject} {self.email_body} {self.text_body}"
        matches = re.findall(pattern, all_text)
        
        return list(set(matches))
    
    def duplicate(self, new_name: str = None):
        """
        Create a duplicate of this template.
        
        Args:
            new_name: Optional new name for the duplicate
            
        Returns:
            The new EmailTemplate instance
        """
        new_template = EmailTemplate(
            organization=self.organization,
            template_name=new_name or f"{self.template_name} (Copy)",
            category=self.category,
            email_subject=self.email_subject,
            preview_text=self.preview_text,
            email_body=self.email_body,
            text_body=self.text_body,
            default_from_name=self.default_from_name,
            default_from_email=self.default_from_email,
            default_reply_to=self.default_reply_to,
            description=self.description,
            tags=self.tags.copy() if self.tags else [],
            variable_schema=self.variable_schema.copy() if self.variable_schema else None,
        )
        new_template.save()
        return new_template

class TemplateUsageLog(models.Model):
    """
    Tracks when organizations duplicate global templates.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # The global template that was duplicated
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.CASCADE,
        related_name='usage_logs',
        help_text="The global template that was used"
    )
    
    # Organization that duplicated it
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='template_usage_logs',
        help_text="Organization that duplicated the template"
    )
    
    # User who performed the duplication
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='template_duplication_logs',
        help_text="User who duplicated the template"
    )
    
    # The resulting duplicated template
    duplicated_template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_usage_logs',
        help_text="The organization-specific template that was created"
    )
    
    # Snapshot data at time of duplication
    duplicated_at = models.DateTimeField(auto_now_add=True)
    template_name_at_duplication = models.CharField(max_length=255)
    template_version_at_duplication = models.IntegerField(default=1)
    
    class Meta:
        indexes = [
            models.Index(fields=['organization', 'duplicated_at']),
            models.Index(fields=['user', 'duplicated_at']),
            models.Index(fields=['template', 'organization']),
        ]
        ordering = ['-duplicated_at']
        verbose_name = "Template Usage Log"
        verbose_name_plural = "Template Usage Logs"
    
    def __str__(self):
        return f"{self.organization.name} used {self.template_name_at_duplication} v{self.template_version_at_duplication}"


class TemplateUpdateNotification(models.Model):
    """
    Tracks notifications about global template updates.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # The global template that was updated
    global_template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.CASCADE,
        related_name='update_notifications',
        help_text="The global template that was updated"
    )
    
    # Version information
    old_version = models.IntegerField(help_text="Previous version number")
    new_version = models.IntegerField(help_text="New version number")
    
    # Notification details
    update_summary = models.TextField(help_text="Summary of changes made in this update")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this notification is still active"
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['global_template', 'created_at']),
            models.Index(fields=['is_active', 'created_at']),
        ]
        ordering = ['-created_at']
        verbose_name = "Template Update Notification"
        verbose_name_plural = "Template Update Notifications"
    
    def __str__(self):
        return f"{self.global_template.template_name} v{self.old_version} → v{self.new_version}"


class OrganizationTemplateNotification(models.Model):
    """
    Tracks which organizations have been notified about template updates
    and whether they've read/acted on the notification.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Related notification
    notification = models.ForeignKey(
        TemplateUpdateNotification,
        on_delete=models.CASCADE,
        related_name='organization_notifications',
        help_text="The template update notification"
    )
    
    # Organization being notified
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='template_notifications',
        help_text="Organization receiving the notification"
    )
    
    # Read status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    read_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='read_template_notifications',
        help_text="User who marked notification as read"
    )
    
    # Action status
    template_updated = models.BooleanField(
        default=False,
        help_text="Whether the organization has updated their copy of the template"
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['organization', 'is_read']),
            models.Index(fields=['notification', 'organization']),
        ]
        unique_together = ['notification', 'organization']
        verbose_name = "Organization Template Notification"
        verbose_name_plural = "Organization Template Notifications"
    
    def __str__(self):
        return f"{self.organization.name} - {self.notification}"


class TemplateApprovalRequest(models.Model):
    """
    Tracks approval requests for global template creation and updates.
    """
    
    class ApprovalStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Template being reviewed
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.CASCADE,
        related_name='approval_requests',
        help_text="Template awaiting approval"
    )
    
    # Requester information
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='template_approval_requests',
        help_text="User who submitted the template for approval"
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    approval_notes = models.TextField(
        blank=True,
        help_text="Notes from the requester about the changes"
    )
    
    # Reviewer information
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_template_approvals',
        help_text="Platform admin who reviewed the request"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING
    )
    reviewer_notes = models.TextField(
        blank=True,
        help_text="Notes from the reviewer"
    )
    
    # Version tracking
    version_before_approval = models.IntegerField(
        help_text="Template version when submitted for approval"
    )
    
    # Changes summary (stores diff of what changed)
    changes_summary = models.JSONField(
        default=dict,
        blank=True,
        help_text="Summary of changes made to the template"
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['status', 'requested_at']),
            models.Index(fields=['template', 'status']),
            models.Index(fields=['requested_by', 'requested_at']),
        ]
        ordering = ['-requested_at']
        verbose_name = "Template Approval Request"
        verbose_name_plural = "Template Approval Requests"
    
    def __str__(self):
        return f"{self.template.template_name} - {self.status} ({self.requested_at.strftime('%Y-%m-%d')})"
    
    def approve(self, reviewer, notes=''):
        """Approve the template and update its status."""
        from django.utils import timezone
        
        self.status = self.ApprovalStatus.APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.reviewer_notes = notes
        self.save()
        
        # Update template approval status
        self.template.approval_status = EmailTemplate.ApprovalStatus.APPROVED
        self.template.is_draft = False
        self.template.approved_by = reviewer
        self.template.approved_at = timezone.now()
        self.template.save()
        
        return self
    
    def reject(self, reviewer, notes=''):
        """Reject the template."""
        from django.utils import timezone
        
        self.status = self.ApprovalStatus.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.reviewer_notes = notes
        self.save()
        
        # Update template approval status
        self.template.approval_status = EmailTemplate.ApprovalStatus.REJECTED
        self.template.save()
        
        return self