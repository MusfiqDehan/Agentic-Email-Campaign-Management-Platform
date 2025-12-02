"""
Email template model for storing reusable email templates.
"""
import uuid
from django.db import models
from apps.utils.base_models import BaseModel
from apps.authentication.models import Organization


class EmailTemplate(BaseModel):
    """
    Stores email templates with dynamic variables.
    
    All templates are organization-scoped (no more GLOBAL/TENANT distinction).
    """
    
    class TemplateCategory(models.TextChoices):
        # Transactional
        EMAIL_VERIFICATION = 'EMAIL_VERIFICATION', 'Email Verification'
        PASSWORD_RESET = 'PASSWORD_RESET', 'Password Reset'
        WELCOME = 'WELCOME', 'Welcome'
        
        # Campaign
        NEWSLETTER = 'NEWSLETTER', 'Newsletter'
        PROMOTIONAL = 'PROMOTIONAL', 'Promotional'
        ANNOUNCEMENT = 'ANNOUNCEMENT', 'Announcement'
        
        # User management
        INVITATION = 'INVITATION', 'Invitation'
        REMINDER = 'REMINDER', 'Reminder'
        NOTIFICATION = 'NOTIFICATION', 'Notification'
        
        # Subscription
        SUBSCRIPTION_CONFIRMATION = 'SUBSCRIPTION_CONFIRMATION', 'Subscription Confirmation'
        SUBSCRIPTION_RENEWAL = 'SUBSCRIPTION_RENEWAL', 'Subscription Renewal'
        
        # Other
        OTHER = 'OTHER', 'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Organization ownership
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='email_templates'
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
    
    # Sender defaults (optional, can be overridden)
    default_from_name = models.CharField(max_length=100, blank=True)
    default_from_email = models.EmailField(blank=True)
    default_reply_to = models.EmailField(blank=True)
    
    # Template metadata
    description = models.TextField(blank=True, help_text="Internal description of this template")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for organizing templates")
    
    # Variable schema (for documentation and validation)
    variable_schema = models.JSONField(
        null=True,
        blank=True,
        help_text="JSON schema describing available variables. Example: {'first_name': 'string', 'company': 'string'}"
    )

    class Meta:
        constraints = [
            # Unique template name per organization
            models.UniqueConstraint(
                fields=['organization', 'template_name'],
                condition=models.Q(is_deleted=False),
                name='unique_template_per_org'
            ),
        ]
        indexes = [
            models.Index(fields=['organization', 'category']),
            models.Index(fields=['organization', 'is_active']),
        ]
        verbose_name = "Email Template"
        verbose_name_plural = "Email Templates"

    def __str__(self):
        return f"{self.template_name} ({self.organization.name})"
    
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
