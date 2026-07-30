"""
Mailbox models for bidirectional email (send + receive) via Gmail IMAP/SMTP and AWS SES.
"""
import uuid
import json
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from apps.utils.base_models import BaseModel
from apps.authentication.models import Organization


class EmailAccount(BaseModel):
    """
    Connected mailbox account for an organization.

    Supports:
    - GMAIL: SMTP send + IMAP receive (app password or OAuth token)
    - AWS_SES: SES send + SES inbound (SNS Received / S3)
    - CUSTOM: arbitrary SMTP + IMAP
    """

    ACCOUNT_TYPES = [
        ('GMAIL', 'Gmail'),
        ('AWS_SES', 'Amazon SES'),
        ('SENDGRID', 'SendGrid'),
        ('BREVO', 'Brevo'),
        ('CUSTOM', 'Custom SMTP/IMAP'),
    ]

    SYNC_STATUS = [
        ('IDLE', 'Idle'),
        ('SYNCING', 'Syncing'),
        ('ERROR', 'Error'),
        ('DISABLED', 'Disabled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='email_accounts',
    )
    name = models.CharField(max_length=100)
    email_address = models.EmailField(db_index=True, validators=[EmailValidator()])
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='GMAIL')
    display_name = models.CharField(max_length=150, blank=True)

    # Encrypted JSON: smtp/imap credentials, SES keys, configuration_set, etc.
    encrypted_config = models.TextField(help_text="Encrypted account configuration")

    # Optional link to an existing EmailProvider used for outbound campaign sends
    email_provider = models.ForeignKey(
        'EmailProvider',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mailbox_accounts',
    )

    # Sync settings
    sync_enabled = models.BooleanField(default=True)
    sync_status = models.CharField(max_length=20, choices=SYNC_STATUS, default='IDLE')
    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_sync_error = models.TextField(blank=True)
    imap_uid_validity = models.BigIntegerField(null=True, blank=True)
    imap_last_uid = models.BigIntegerField(null=True, blank=True, default=0)

    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'email_address'],
                name='unique_mailbox_email_per_org',
            ),
        ]
        indexes = [
            models.Index(fields=['organization', 'account_type']),
            models.Index(fields=['organization', 'is_default']),
        ]
        verbose_name = "Email Account"
        verbose_name_plural = "Email Accounts"

    def __str__(self):
        return f"{self.name} <{self.email_address}> ({self.account_type})"

    def save(self, *args, **kwargs):
        if self.is_default:
            EmailAccount.objects.filter(
                organization=self.organization,
                is_default=True,
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def encrypt_config(self, config_dict):
        try:
            from ..utils.crypto import encrypt_data
            self.encrypted_config = encrypt_data(json.dumps(config_dict))
        except Exception as e:
            raise ValidationError(f"Failed to encrypt configuration: {str(e)}")

    def decrypt_config(self):
        try:
            if not self.encrypted_config:
                return {}
            from ..utils.crypto import decrypt_data
            return json.loads(decrypt_data(self.encrypted_config))
        except Exception as e:
            raise ValidationError(f"Failed to decrypt configuration: {str(e)}")

    def get_smtp_defaults(self):
        """Return sensible SMTP defaults for known account types."""
        if self.account_type == 'GMAIL':
            return {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'use_tls': True,
                'use_ssl': False,
                'imap_server': 'imap.gmail.com',
                'imap_port': 993,
            }
        return {}


class MailboxMessage(BaseModel):
    """Individual inbound or outbound mailbox message (Gmail-like inbox)."""

    DIRECTIONS = [
        ('INBOUND', 'Inbound'),
        ('OUTBOUND', 'Outbound'),
    ]

    FOLDERS = [
        ('INBOX', 'Inbox'),
        ('SENT', 'Sent'),
        ('DRAFTS', 'Drafts'),
        ('ARCHIVE', 'Archive'),
        ('TRASH', 'Trash'),
        ('SPAM', 'Spam'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='mailbox_messages',
    )
    account = models.ForeignKey(
        EmailAccount,
        on_delete=models.CASCADE,
        related_name='messages',
    )

    direction = models.CharField(max_length=10, choices=DIRECTIONS, db_index=True)
    folder = models.CharField(max_length=20, choices=FOLDERS, default='INBOX', db_index=True)

    # RFC identifiers for threading
    message_id = models.CharField(max_length=512, blank=True, db_index=True)
    in_reply_to = models.CharField(max_length=512, blank=True, db_index=True)
    references = models.TextField(blank=True)
    thread_key = models.CharField(max_length=512, blank=True, db_index=True)

    from_address = models.EmailField(db_index=True)
    from_name = models.CharField(max_length=255, blank=True)
    to_addresses = models.JSONField(default=list)
    cc_addresses = models.JSONField(default=list, blank=True)
    bcc_addresses = models.JSONField(default=list, blank=True)
    reply_to = models.EmailField(blank=True)

    subject = models.CharField(max_length=998, blank=True)
    text_body = models.TextField(blank=True)
    html_body = models.TextField(blank=True)
    snippet = models.CharField(max_length=255, blank=True)

    # Provider / IMAP metadata
    provider_message_id = models.CharField(max_length=512, blank=True, db_index=True)
    imap_uid = models.BigIntegerField(null=True, blank=True)
    raw_headers = models.JSONField(default=dict, blank=True)
    attachments_meta = models.JSONField(default=list, blank=True)

    is_read = models.BooleanField(default=False, db_index=True)
    is_starred = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=False)

    sent_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True, db_index=True)

    # Link to campaign delivery when this is a marketing send
    delivery_log = models.ForeignKey(
        'EmailDeliveryLog',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mailbox_messages',
    )
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
    )

    class Meta:
        ordering = ['-received_at', '-sent_at', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'folder', 'is_read']),
            models.Index(fields=['account', 'folder', 'received_at']),
            models.Index(fields=['account', 'message_id']),
            models.Index(fields=['thread_key']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['account', 'message_id'],
                condition=~models.Q(message_id=''),
                name='unique_message_id_per_account',
            ),
        ]
        verbose_name = "Mailbox Message"
        verbose_name_plural = "Mailbox Messages"

    def __str__(self):
        return f"[{self.direction}] {self.subject[:60]} ({self.from_address})"

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read', 'updated_at'])
