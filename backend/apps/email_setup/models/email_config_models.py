
import uuid
from django.db import models
from django.core.exceptions import ValidationError
from core import BaseModel


class EmailTemplate(BaseModel):
    """
    Stores email templates with dynamic variables.

    Attributes:
        template_name (str): Unique name for the email template.
        email_subject (str): Subject line of the email.
        email_body (str): Body of the email, can include dynamic variables like {{variable_name}}.
        recipient_emails_list (str): Comma-separated list of recipient email addresses.
        template_type (str): Whether this is a global or tenant-specific template.
        category (str): Template category for organization.
    """
    
    class TemplateType(models.TextChoices):
        TENANT = 'TENANT', 'Tenant Specific'
        GLOBAL = 'GLOBAL', 'Global Organization'
    
    class TemplateCategory(models.TextChoices):
        TEST_TMD_INVITATION_SENT = 'TEST_TMD_INVITATION_SENT', 'Test TMD Invitation Sent'
        TENANT_OTP_VERIFICATION = 'TENANT_OTP_VERIFICATION', 'Tenant OTP Verification'
        TENANT_REGISTRATION_CONFIRMATION = 'TENANT_REGISTRATION_CONFIRMATION', 'Tenant Registration Confirmation'
        TENANT_SUBSCRIPTION_CONFIRMATION = 'TENANT_SUBSCRIPTION_CONFIRMATION', 'Tenant Subscription Confirmation'
        EMPLOYEE_WELCOME_EMAIL = 'EMPLOYEE_WELCOME_EMAIL', 'Employee Welcome Email'
        CANDIDATE_EMAIL_VERIFICATION = 'CANDIDATE_EMAIL_VERIFICATION', 'Candidate Email Verification'
        INVITATION_SENT = 'INVITATION_SENT', 'Invitation Sent'
        INVITATION_RESEND = 'INVITATION_RESEND', 'Invitation Resend'
        INVITATION_UPDATE = 'INVITATION_UPDATE', 'Invitation Update'
        INVITATION_ACTIVATION = 'INVITATION_ACTIVATION', 'Invitation Activation'
        INVITATION_DEACTIVATION = 'INVITATION_DEACTIVATION', 'Invitation Deactivation'
        PASSWORD_RESET = 'PASSWORD_RESET', 'Password Reset'
        ROLE_EXPIRATION_REMINDER = 'ROLE_EXPIRATION_REMINDER', 'Role Expiration Reminder'
        INVITATION_EXPIRATION_REMINDER = 'INVITATION_EXPIRATION_REMINDER', 'Invitation Expiration Reminder'
        OTHER = 'OTHER', 'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template_name = models.CharField(max_length=255)
    tenant_id = models.UUIDField(blank=True, null=True, help_text="Tenant-specific template if set (null for global templates).")
    template_type = models.CharField(max_length=100, choices=TemplateType.choices, default=TemplateType.TENANT, help_text="Whether this template is global or tenant-specific")
    category = models.CharField(max_length=100, choices=TemplateCategory.choices, default=TemplateCategory.OTHER, help_text="Template category for organization")
    email_subject = models.CharField(max_length=255)
    email_body = models.TextField(help_text="Use {{variable_name}} for dynamic content.")
    # Storing recipient_emails as a comma-separated string for flexibility
    recipient_emails_list = models.TextField(blank=True, help_text="Comma-separated email addresses.")

    class Meta(BaseModel.Meta):
        constraints = [
            # Unique template name per tenant
            models.UniqueConstraint(
                fields=['template_name', 'tenant_id'],
                condition=models.Q(tenant_id__isnull=False),
                name='unique_template_per_tenant'
            ),
            # Unique global template name
            models.UniqueConstraint(
                fields=['template_name'],
                condition=models.Q(tenant_id__isnull=True),
                name='unique_global_template'
            ),
        ]

    def clean(self):
        """Validate template type consistency with tenant_id"""
        super().clean()
        if self.template_type == self.TemplateType.GLOBAL and self.tenant_id is not None:
            raise ValidationError("Global templates cannot have a tenant_id")
        if self.template_type == self.TemplateType.TENANT and self.tenant_id is None:
            raise ValidationError("Tenant templates must have a tenant_id")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        scope = "Global" if self.template_type == self.TemplateType.GLOBAL else f"Tenant-{self.tenant_id}"
        return f"{self.template_name} ({scope})"
