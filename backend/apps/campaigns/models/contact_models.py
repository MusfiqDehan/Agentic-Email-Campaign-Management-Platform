"""
Contact and ContactList models for email campaign management.
"""
import uuid
import secrets
from django.db import models
from django.utils import timezone
from apps.utils.base_models import BaseModel
from apps.authentication.models import Organization


class ContactList(BaseModel):
    """
    A list of contacts for organizing campaign recipients.
    
    Contacts can belong to multiple lists, and lists are organization-scoped.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='contact_lists'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # List settings
    double_opt_in = models.BooleanField(
        default=False, 
        help_text="Require email confirmation before adding contacts"
    )
    
    # Statistics (denormalized for performance)
    total_contacts = models.PositiveIntegerField(default=0)
    active_contacts = models.PositiveIntegerField(default=0)
    unsubscribed_contacts = models.PositiveIntegerField(default=0)
    bounced_contacts = models.PositiveIntegerField(default=0)
    
    # Metadata
    tags = models.JSONField(default=list, blank=True, help_text="List of tags for categorization")
    
    class Meta:
        verbose_name = "Contact List"
        verbose_name_plural = "Contact Lists"
        unique_together = ['organization', 'name']
        indexes = [
            models.Index(fields=['organization', 'name']),
            models.Index(fields=['organization', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"
    
    def update_stats(self):
        """Recalculate statistics from actual contact counts."""
        from django.db.models import Count, Q
        stats = self.contacts.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='ACTIVE')),
            unsubscribed=Count('id', filter=Q(status='UNSUBSCRIBED')),
            bounced=Count('id', filter=Q(status='BOUNCED')),
        )
        self.total_contacts = stats['total'] or 0
        self.active_contacts = stats['active'] or 0
        self.unsubscribed_contacts = stats['unsubscribed'] or 0
        self.bounced_contacts = stats['bounced'] or 0
        self.save(update_fields=[
            'total_contacts', 'active_contacts', 
            'unsubscribed_contacts', 'bounced_contacts'
        ])


class Contact(BaseModel):
    """
    Individual contact for email campaigns.
    
    Contacts are organization-scoped and can belong to multiple lists.
    Each contact has a unique unsubscribe_token for GDPR-compliant unsubscription.
    """
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('UNSUBSCRIBED', 'Unsubscribed'),
        ('BOUNCED', 'Bounced'),
        ('COMPLAINED', 'Complained'),
        ('PENDING', 'Pending Verification'),
    ]
    
    SOURCE_CHOICES = [
        ('MANUAL', 'Manual Entry'),
        ('CSV_IMPORT', 'CSV Import'),
        ('JSON_IMPORT', 'JSON Import'),
        ('API', 'API'),
        ('SIGNUP_FORM', 'Signup Form'),
        ('MIGRATION', 'Migration'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='contacts'
    )
    
    # Core contact information
    email = models.EmailField(db_index=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # List membership (many-to-many)
    lists = models.ManyToManyField(
        ContactList, 
        related_name='contacts',
        blank=True
    )
    
    # Status and subscription
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', db_index=True)
    unsubscribe_token = models.CharField(
        max_length=64, 
        unique=True, 
        editable=False,
        help_text="Unique token for unsubscribe links"
    )
    
    # Subscription timestamps
    subscribed_at = models.DateTimeField(default=timezone.now)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True, help_text="For double opt-in")
    
    # Source tracking
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='MANUAL')
    source_details = models.JSONField(
        null=True, 
        blank=True, 
        help_text="Additional details about the source (e.g., import file name)"
    )
    
    # Custom fields for flexibility
    custom_fields = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Custom contact attributes"
    )
    
    # Engagement tracking (denormalized for performance)
    emails_sent = models.PositiveIntegerField(default=0)
    emails_opened = models.PositiveIntegerField(default=0)
    emails_clicked = models.PositiveIntegerField(default=0)
    last_email_sent_at = models.DateTimeField(null=True, blank=True)
    last_email_opened_at = models.DateTimeField(null=True, blank=True)
    last_email_clicked_at = models.DateTimeField(null=True, blank=True)
    
    # Bounce/complaint tracking
    bounce_count = models.PositiveIntegerField(default=0)
    complaint_count = models.PositiveIntegerField(default=0)
    last_bounce_at = models.DateTimeField(null=True, blank=True)
    last_complaint_at = models.DateTimeField(null=True, blank=True)
    bounce_reason = models.TextField(blank=True)
    
    # Tags for segmentation
    tags = models.JSONField(default=list, blank=True, help_text="List of tags for segmentation")
    
    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        unique_together = ['organization', 'email']
        indexes = [
            models.Index(fields=['organization', 'email']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'is_active', 'status']),
            models.Index(fields=['unsubscribe_token']),
            models.Index(fields=['organization', 'source']),
        ]
    
    def __str__(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return f"{name} <{self.email}>" if name else self.email
    
    def save(self, *args, **kwargs):
        # Generate unsubscribe token if not set
        if not self.unsubscribe_token:
            self.unsubscribe_token = secrets.token_urlsafe(48)
        super().save(*args, **kwargs)
    
    @property
    def full_name(self):
        """Return the full name of the contact."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def open_rate(self):
        """Calculate open rate percentage."""
        if self.emails_sent == 0:
            return 0.0
        return (self.emails_opened / self.emails_sent) * 100
    
    @property
    def click_rate(self):
        """Calculate click rate percentage."""
        if self.emails_sent == 0:
            return 0.0
        return (self.emails_clicked / self.emails_sent) * 100
    
    def unsubscribe(self, reason: str = ""):
        """Mark contact as unsubscribed."""
        self.status = 'UNSUBSCRIBED'
        self.unsubscribed_at = timezone.now()
        if reason:
            if not self.custom_fields:
                self.custom_fields = {}
            self.custom_fields['unsubscribe_reason'] = reason
        self.save(update_fields=['status', 'unsubscribed_at', 'custom_fields'])
        
        # Update list statistics
        for contact_list in self.lists.all():
            contact_list.update_stats()
    
    def mark_bounced(self, reason: str = "", bounce_type: str = "HARD"):
        """Mark contact as bounced."""
        self.status = 'BOUNCED'
        self.bounce_count += 1
        self.last_bounce_at = timezone.now()
        self.bounce_reason = reason
        self.save(update_fields=['status', 'bounce_count', 'last_bounce_at', 'bounce_reason'])
        
        # Update list statistics
        for contact_list in self.lists.all():
            contact_list.update_stats()
    
    def mark_complained(self):
        """Mark contact as complained (spam report)."""
        self.status = 'COMPLAINED'
        self.complaint_count += 1
        self.last_complaint_at = timezone.now()
        self.save(update_fields=['status', 'complaint_count', 'last_complaint_at'])
        
        # Update list statistics
        for contact_list in self.lists.all():
            contact_list.update_stats()
    
    def record_email_sent(self):
        """Record that an email was sent to this contact."""
        self.emails_sent += 1
        self.last_email_sent_at = timezone.now()
        self.save(update_fields=['emails_sent', 'last_email_sent_at'])
    
    def record_email_opened(self):
        """Record that the contact opened an email."""
        self.emails_opened += 1
        self.last_email_opened_at = timezone.now()
        self.save(update_fields=['emails_opened', 'last_email_opened_at'])
    
    def record_email_clicked(self):
        """Record that the contact clicked a link in an email."""
        self.emails_clicked += 1
        self.last_email_clicked_at = timezone.now()
        self.save(update_fields=['emails_clicked', 'last_email_clicked_at'])
    
    def forget(self):
        """
        GDPR forget - anonymize contact data while preserving statistics.
        """
        import hashlib
        
        # Create anonymized email hash for deduplication
        email_hash = hashlib.sha256(self.email.encode()).hexdigest()[:16]
        
        # Anonymize PII
        self.email = f"forgotten_{email_hash}@forgotten.local"
        self.first_name = "FORGOTTEN"
        self.last_name = ""
        self.phone = ""
        self.custom_fields = {"gdpr_forgotten": True, "forgotten_at": timezone.now().isoformat()}
        self.status = 'UNSUBSCRIBED'
        self.is_active = False
        
        # Generate new unsubscribe token to invalidate old links
        self.unsubscribe_token = secrets.token_urlsafe(48)
        
        self.save()
        
        # Remove from all lists
        self.lists.clear()
