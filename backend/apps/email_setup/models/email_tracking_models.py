import uuid
from django.db import models
from django.core.validators import EmailValidator
from core import BaseModel


class EmailValidation(BaseModel):
    """Email validation and quality checks"""
    
    VALIDATION_STATUS = [
        ('VALID', 'Valid'),
        ('INVALID', 'Invalid'),
        ('RISKY', 'Risky'),
        ('UNKNOWN', 'Unknown'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email_address = models.EmailField(unique=True, db_index=True, validators=[EmailValidator()])
    
    # Validation results
    is_valid_format = models.BooleanField(default=True)
    is_disposable = models.BooleanField(default=False)
    is_role_based = models.BooleanField(default=False, help_text="info@, admin@, support@, etc.")
    domain_mx_valid = models.BooleanField(default=True)
    
    validation_status = models.CharField(max_length=10, choices=VALIDATION_STATUS, default='UNKNOWN')
    validation_score = models.FloatField(null=True, blank=True, help_text="Validation score 0-100")
    
    # Reputation tracking
    bounce_count = models.PositiveIntegerField(default=0)
    complaint_count = models.PositiveIntegerField(default=0)
    successful_deliveries = models.PositiveIntegerField(default=0)
    
    # Blacklist status
    is_blacklisted = models.BooleanField(default=False)
    blacklist_reason = models.TextField(blank=True)
    blacklisted_at = models.DateTimeField(null=True, blank=True)
    
    # Validation metadata
    last_validated_at = models.DateTimeField(auto_now=True)
    validation_provider = models.CharField(max_length=50, blank=True, help_text="Service used for validation")
    
    def calculate_reputation_score(self):
        """Calculate email reputation score based on delivery history"""
        total_attempts = self.bounce_count + self.complaint_count + self.successful_deliveries
        if total_attempts == 0:
            return 100.0  # New email, assume good
        
        success_rate = (self.successful_deliveries / total_attempts) * 100
        bounce_penalty = (self.bounce_count / total_attempts) * 50
        complaint_penalty = (self.complaint_count / total_attempts) * 80
        
        score = success_rate - bounce_penalty - complaint_penalty
        return max(0.0, min(100.0, score))  # Clamp between 0-100
    
    def update_reputation(self, event_type):
        """Update reputation based on delivery event"""
        if event_type == 'delivered':
            self.successful_deliveries += 1
        elif event_type == 'bounced':
            self.bounce_count += 1
        elif event_type == 'complained':
            self.complaint_count += 1
        
        # Recalculate validation score
        self.validation_score = self.calculate_reputation_score()
        
        # Update validation status based on score
        if self.validation_score >= 80:
            self.validation_status = 'VALID'
        elif self.validation_score >= 50:
            self.validation_status = 'RISKY'
        else:
            self.validation_status = 'INVALID'
        
        self.save()
    
    class Meta:
        indexes = [
            models.Index(fields=['email_address']),
            models.Index(fields=['validation_status', 'is_blacklisted']),
            models.Index(fields=['is_blacklisted', 'last_validated_at']),
        ]
        verbose_name = "Email Validation"
        verbose_name_plural = "Email Validations"
    
    def __str__(self):
        return f"{self.email_address} ({self.validation_status})"


class EmailQueue(BaseModel):
    """Email queue for batch processing and retry management"""
    
    QUEUE_STATUS = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('RETRYING', 'Retrying'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships - reference tenant by ID only
    automation_rule = models.ForeignKey(
        'AutomationRule', 
        on_delete=models.CASCADE, 
        related_name='queued_emails'
    )
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True, help_text="Reference to tenant from tenant microservice (null for global emails)")
    
    # Email details
    recipient_email = models.EmailField(db_index=True)
    subject = models.CharField(max_length=255)
    html_content = models.TextField()
    text_content = models.TextField(blank=True)
    
    # Metadata
    context_data = models.JSONField(null=True, blank=True, help_text="Template variables and context")
    headers = models.JSONField(null=True, blank=True, help_text="Custom email headers")
    
    # Processing details
    status = models.CharField(max_length=20, choices=QUEUE_STATUS, default='PENDING', db_index=True)
    priority = models.PositiveIntegerField(default=5, help_text="1=highest, 10=lowest")
    
    # Scheduling
    scheduled_at = models.DateTimeField(db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Retry logic
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    error_code = models.CharField(max_length=50, blank=True)
    
    # Provider tracking
    assigned_provider = models.ForeignKey(
        'EmailProvider', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    class Meta:
        ordering = ['priority', 'scheduled_at']
        indexes = [
            models.Index(fields=['status', 'scheduled_at']),
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'automation_rule', 'status']),
            models.Index(fields=['scheduled_at', 'priority']),
        ]
        verbose_name = "Email Queue Item"
        verbose_name_plural = "Email Queue"
    
    def __str__(self):
        return f"Email to {self.recipient_email} - {self.status}"


class EmailDeliveryLog(BaseModel):
    """Comprehensive email delivery tracking and analytics"""
    
    DELIVERY_STATUS = [
        ('QUEUED', 'Queued'),
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('BOUNCED', 'Bounced'),
        ('COMPLAINED', 'Complained'),
        ('OPENED', 'Opened'),
        ('CLICKED', 'Clicked'),
        ('UNSUBSCRIBED', 'Unsubscribed'),
        ('FAILED', 'Failed'),
    ]
    
    BOUNCE_TYPES = [
        ('HARD', 'Hard Bounce'),
        ('SOFT', 'Soft Bounce'),
        ('COMPLAINT', 'Complaint'),
    ]

    LOG_SCOPE_CHOICES = [
        ('TENANT', 'Tenant'),
        ('GLOBAL', 'Global'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    queue_item = models.OneToOneField(
        EmailQueue, 
        on_delete=models.CASCADE, 
        related_name='delivery_log',
        null=True,
        blank=True
    )
    automation_rule = models.ForeignKey(
        'AutomationRule', 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True
    )
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True, help_text="Reference to tenant from tenant microservice")
    product_id = models.UUIDField(null=True, blank=True, db_index=True, help_text="Associated product for this dispatch")
    reason_name = models.CharField(max_length=100, blank=True, help_text="Snapshot of automation reason at send time")
    trigger_type = models.CharField(max_length=20, blank=True, help_text="Snapshot of trigger type at send time")
    email_template = models.ForeignKey(
        'EmailTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Email template used when rendering the message"
    )
    email_validation = models.ForeignKey(
        EmailValidation, 
        on_delete=models.SET_NULL, 
        null=True
    )
    
    # Provider information
    email_provider = models.ForeignKey(
        'EmailProvider', 
        on_delete=models.SET_NULL, 
        null=True
    )
    provider_message_id = models.CharField(max_length=255, blank=True, db_index=True)
    
    # Email details snapshot
    recipient_email = models.EmailField(db_index=True)
    sender_email = models.EmailField(blank=True)
    subject = models.CharField(max_length=255, blank=True)
    
    # Delivery tracking
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS, db_index=True)
    log_scope = models.CharField(max_length=10, choices=LOG_SCOPE_CHOICES, default='TENANT', db_index=True)
    
    # Timestamps
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    bounced_at = models.DateTimeField(null=True, blank=True)
    planned_delivery_at = models.DateTimeField(null=True, blank=True)
    
    # Engagement metrics
    open_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)
    unique_click_count = models.PositiveIntegerField(default=0)
    
    # Error details
    bounce_type = models.CharField(max_length=20, choices=BOUNCE_TYPES, blank=True)
    bounce_reason = models.TextField(blank=True)
    
    # Spam detection
    spam_score = models.FloatField(null=True, blank=True)
    is_spam = models.BooleanField(default=False)
    
    # Duplicate detection
    is_duplicate = models.BooleanField(default=False)
    duplicate_of = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='duplicates'
    )
    
    # Additional metadata
    user_agent = models.TextField(blank=True, help_text="User agent for opens/clicks")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    event_history = models.JSONField(default=list, blank=True, help_text="Chronological list of provider events")
    context_data = models.JSONField(default=dict, blank=True, null=True, help_text="Template variables used for rendering")
    error_message = models.TextField(blank=True, help_text="Error information for failed sends")
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant_id', 'delivery_status']),
            models.Index(fields=['tenant_id', 'sent_at']),
            models.Index(fields=['recipient_email', 'sent_at']),
            models.Index(fields=['automation_rule', 'sent_at']),
            models.Index(fields=['delivery_status', 'sent_at']),
            models.Index(fields=['provider_message_id']),
            models.Index(fields=['log_scope', 'sent_at']),
            models.Index(fields=['product_id', 'sent_at']),
            models.Index(fields=['email_template', 'sent_at']),
        ]
        verbose_name = "Email Delivery Log"
        verbose_name_plural = "Email Delivery Logs"
    
    def __str__(self):
        scope = self.log_scope or 'TENANT'
        return f"[{scope}] Email to {self.recipient_email} - {self.delivery_status}"


class EmailAction(BaseModel):
    """Track email actions like resend, forward, etc."""
    
    ACTION_TYPES = [
        ('RESEND', 'Resend'),
        ('FORWARD', 'Forward'),
        ('CANCEL', 'Cancel'),
        ('ARCHIVE', 'Archive'),
        ('SUPPRESS', 'Suppress'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    original_log = models.ForeignKey(
        EmailDeliveryLog, 
        on_delete=models.CASCADE, 
        related_name='actions'
    )
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    
    # For forwards/resends
    new_recipient = models.EmailField(null=True, blank=True)
    new_delivery_log = models.ForeignKey(
        EmailDeliveryLog, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='source_actions'
    )
    
    # Action metadata
    reason = models.TextField(blank=True)
    performed_by = models.UUIDField(null=True, blank=True, help_text="User ID who performed the action")
    
    performed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['original_log', 'action_type']),
            models.Index(fields=['performed_at', 'action_type']),
        ]
        verbose_name = "Email Action"
        verbose_name_plural = "Email Actions"
    
    def __str__(self):
        return f"{self.action_type} - {self.original_log.recipient_email}"