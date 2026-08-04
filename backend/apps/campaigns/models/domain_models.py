"""
Sending domains and dynamic sender email addresses backed by AWS SES.

An organization registers a SendingDomain; the platform provisions it as an
SES identity (DKIM) either in the platform's central AWS account
(ownership_mode=PLATFORM) or in the org's own SES account via its
EmailProvider credentials (ownership_mode=ORG). Once SES reports the domain
verified, the org can create SenderEmail addresses under it, up to the
package limit. Platform admins can suspend domains and addresses at any time.
"""
import re
import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from apps.utils.base_models import BaseModel
from apps.authentication.models import Organization

# Simple RFC-adjacent validators; SES enforces the rest at provisioning time.
DOMAIN_RE = re.compile(
    r'^(?=.{4,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$'
)
LOCAL_PART_RE = re.compile(r'^[a-z0-9](?:[a-z0-9._+-]{0,62}[a-z0-9])?$')


class SendingDomain(BaseModel):
    """A domain registered by an organization for sending (and receiving) email via SES."""

    OWNERSHIP_PLATFORM = 'PLATFORM'
    OWNERSHIP_ORG = 'ORG'
    OWNERSHIP_CHOICES = [
        (OWNERSHIP_PLATFORM, 'Platform-managed SES account'),
        (OWNERSHIP_ORG, "Organization's own SES account"),
    ]

    STATUS_PENDING_DNS = 'PENDING_DNS'
    STATUS_PENDING_VERIFICATION = 'PENDING_VERIFICATION'
    STATUS_VERIFIED = 'VERIFIED'
    STATUS_FAILED = 'FAILED'
    STATUS_SUSPENDED = 'SUSPENDED'
    STATUS_DISABLED = 'DISABLED'
    STATUS_CHOICES = [
        (STATUS_PENDING_DNS, 'Pending DNS setup'),
        (STATUS_PENDING_VERIFICATION, 'Pending verification'),
        (STATUS_VERIFIED, 'Verified'),
        (STATUS_FAILED, 'Verification failed'),
        (STATUS_SUSPENDED, 'Suspended by platform admin'),
        (STATUS_DISABLED, 'Disabled'),
    ]
    PENDING_STATUSES = [STATUS_PENDING_DNS, STATUS_PENDING_VERIFICATION]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='sending_domains'
    )
    domain = models.CharField(max_length=253, db_index=True)
    ownership_mode = models.CharField(
        max_length=20, choices=OWNERSHIP_CHOICES, default=OWNERSHIP_PLATFORM
    )
    provider = models.ForeignKey(
        'campaigns.EmailProvider', null=True, blank=True, on_delete=models.PROTECT,
        related_name='sending_domains',
        help_text="Org-owned AWS SES provider holding the identity (required for ownership_mode=ORG)"
    )
    region = models.CharField(max_length=30, blank=True, default='')

    status = models.CharField(
        max_length=25, choices=STATUS_CHOICES, default=STATUS_PENDING_DNS, db_index=True
    )
    # Status held before an admin suspension, restored on reactivate
    previous_status = models.CharField(max_length=25, blank=True, default='')

    dkim_tokens = models.JSONField(default=list, blank=True)
    dns_records = models.JSONField(
        default=list, blank=True,
        help_text="Display list of records the org must publish: [{type, name, value, purpose}]"
    )
    mail_from_subdomain = models.CharField(max_length=63, default='mail')
    mail_from_status = models.CharField(max_length=30, blank=True, default='')

    verified_at = models.DateTimeField(null=True, blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    verification_error = models.TextField(blank=True, default='')
    suspension_reason = models.TextField(blank=True, default='')
    legacy = models.BooleanField(
        default=False, help_text="Migrated from the old OrganizationEmailConfiguration.custom_domain field"
    )

    class Meta:
        verbose_name = "Sending Domain"
        verbose_name_plural = "Sending Domains"
        constraints = [
            models.UniqueConstraint(
                fields=['domain'],
                condition=Q(is_deleted=False),
                name='uniq_active_sending_domain',
            ),
        ]
        indexes = [
            models.Index(fields=['organization', 'status']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.domain} ({self.organization.name}, {self.status})"

    def clean(self):
        super().clean()
        self.domain = (self.domain or '').strip().lower().rstrip('.')
        if not DOMAIN_RE.match(self.domain):
            raise ValidationError({'domain': 'Enter a valid domain name (e.g. example.com).'})
        if self.ownership_mode == self.OWNERSHIP_ORG:
            if not self.provider_id:
                raise ValidationError({'provider': 'An AWS SES provider is required for org-owned domains.'})
            if self.provider.provider_type != 'AWS_SES':
                raise ValidationError({'provider': 'Provider must be an AWS SES provider.'})
            if self.provider.organization_id != self.organization_id:
                raise ValidationError({'provider': 'Provider must belong to your organization.'})

    def save(self, *args, **kwargs):
        self.domain = (self.domain or '').strip().lower().rstrip('.')
        super().save(*args, **kwargs)

    @property
    def is_usable(self):
        """Whether sender emails on this domain may send right now."""
        if self.is_deleted or self.status != self.STATUS_VERIFIED or not self.is_active:
            return False
        config = getattr(self.organization, 'email_configuration', None)
        if config is not None and not config.domain_feature_enabled:
            return False
        return True

    @property
    def mail_from_domain(self):
        return f"{self.mail_from_subdomain}.{self.domain}"


class SenderEmail(BaseModel):
    """A sender address (local_part@domain) an organization created under a verified domain."""

    STATUS_ACTIVE = 'ACTIVE'
    STATUS_SUSPENDED = 'SUSPENDED'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_SUSPENDED, 'Suspended by platform admin'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='sender_emails'
    )
    domain = models.ForeignKey(
        SendingDomain, on_delete=models.CASCADE, related_name='sender_emails'
    )
    local_part = models.CharField(max_length=64)
    email_address = models.EmailField(max_length=320, db_index=True)
    display_name = models.CharField(max_length=120, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    suspension_reason = models.TextField(blank=True, default='')
    mailbox_account = models.OneToOneField(
        'campaigns.EmailAccount', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='sender_email',
        help_text="Auto-created inbox account (platform-managed domains only)"
    )

    class Meta:
        verbose_name = "Sender Email"
        verbose_name_plural = "Sender Emails"
        constraints = [
            models.UniqueConstraint(
                fields=['email_address'],
                condition=Q(is_deleted=False),
                name='uniq_active_sender_email',
            ),
        ]
        indexes = [
            models.Index(fields=['organization', 'status']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email_address} ({self.status})"

    def clean(self):
        super().clean()
        self.local_part = (self.local_part or '').strip().lower()
        if not LOCAL_PART_RE.match(self.local_part):
            raise ValidationError({
                'local_part': 'Use letters, digits and . _ + - (must start/end with a letter or digit).'
            })

    def save(self, *args, **kwargs):
        self.local_part = (self.local_part or '').strip().lower()
        if self.domain_id and self.local_part:
            self.email_address = f"{self.local_part}@{self.domain.domain}"
        super().save(*args, **kwargs)

    @property
    def is_usable(self):
        """Whether this address may send right now."""
        return (
            not self.is_deleted
            and self.is_active
            and self.status == self.STATUS_ACTIVE
            and self.domain.is_usable
        )


class DomainAuditLog(models.Model):
    """Audit trail for domain / sender-email / package actions (mirrors ProviderAuditLog)."""

    ACTION_CHOICES = [
        ('created', 'Created'),
        ('verified', 'Verified'),
        ('verification_failed', 'Verification failed'),
        ('suspended', 'Suspended'),
        ('reactivated', 'Reactivated'),
        ('deleted', 'Deleted'),
        ('package_assigned', 'Package assigned'),
        ('limits_overridden', 'Limits overridden'),
        ('feature_toggled', 'Feature toggled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='domain_audit_logs'
    )
    object_type = models.CharField(max_length=40)
    object_id = models.CharField(max_length=64)
    object_repr = models.CharField(max_length=255, blank=True, default='')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    details = models.JSONField(default=dict, blank=True)
    actor = models.ForeignKey(
        'authentication.User', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='domain_audit_logs'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Domain Audit Log"
        verbose_name_plural = "Domain Audit Logs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', '-created_at']),
            models.Index(fields=['object_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.action} {self.object_type} {self.object_repr}"

    @classmethod
    def log(cls, obj, action, actor=None, organization=None, details=None):
        return cls.objects.create(
            organization=organization or getattr(obj, 'organization', None),
            object_type=obj.__class__.__name__,
            object_id=str(obj.pk),
            object_repr=str(obj)[:255],
            action=action,
            details=details or {},
            actor=actor,
        )
