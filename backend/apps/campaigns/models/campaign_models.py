"""
Campaign model for email campaign management.
"""
import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from apps.utils.base_models import BaseModel
from apps.authentication.models import Organization


class Campaign(BaseModel):
    """
    Email campaign model with inline statistics.
    
    Campaigns are organization-scoped and can target one or more contact lists.
    Statistics are stored inline for efficient querying and display.
    """
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SCHEDULED', 'Scheduled'),
        ('SENDING', 'Sending'),
        ('SENT', 'Sent'),
        ('PAUSED', 'Paused'),
        ('CANCELLED', 'Cancelled'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='campaigns'
    )
    
    # Campaign basics
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Email content
    subject = models.CharField(max_length=255)
    preview_text = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Preview text shown in email clients"
    )
    html_content = models.TextField(help_text="HTML email body")
    text_content = models.TextField(blank=True, help_text="Plain text fallback")
    
    # Sender information
    from_name = models.CharField(max_length=100)
    from_email = models.EmailField()
    reply_to = models.EmailField(blank=True)
    
    # Template reference (optional, for template-based campaigns)
    email_template = models.ForeignKey(
        'EmailTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campaigns'
    )
    
    # Target lists (many-to-many)
    contact_lists = models.ManyToManyField(
        'ContactList',
        related_name='campaigns',
        blank=True
    )
    
    # Provider configuration
    email_provider = models.ForeignKey(
        'OrganizationEmailProvider',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campaigns',
        help_text="Specific provider to use (defaults to organization primary)"
    )
    
    # Campaign status
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='DRAFT',
        db_index=True
    )
    
    # Scheduling
    scheduled_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When to send the campaign (stored in UTC)"
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Celery Beat integration
    periodic_task = models.OneToOneField(
        PeriodicTask, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    # Inline statistics (denormalized for efficient display)
    stats_total_recipients = models.PositiveIntegerField(default=0)
    stats_sent = models.PositiveIntegerField(default=0)
    stats_delivered = models.PositiveIntegerField(default=0)
    stats_opened = models.PositiveIntegerField(default=0)
    stats_clicked = models.PositiveIntegerField(default=0)
    stats_bounced = models.PositiveIntegerField(default=0)
    stats_complained = models.PositiveIntegerField(default=0)
    stats_unsubscribed = models.PositiveIntegerField(default=0)
    stats_failed = models.PositiveIntegerField(default=0)
    
    # Unique counts for open/click
    stats_unique_opens = models.PositiveIntegerField(default=0)
    stats_unique_clicks = models.PositiveIntegerField(default=0)
    
    # Stats last updated timestamp
    stats_updated_at = models.DateTimeField(null=True, blank=True)
    
    # Sending configuration
    batch_size = models.PositiveIntegerField(
        default=100,
        help_text="Number of emails to send per batch"
    )
    batch_delay_seconds = models.PositiveIntegerField(
        default=0,
        help_text="Delay between batches in seconds"
    )
    
    # Tracking settings
    track_opens = models.BooleanField(default=True)
    track_clicks = models.BooleanField(default=True)
    
    # Tags for organization
    tags = models.JSONField(default=list, blank=True)
    
    # Metadata for filtering/segmentation
    segment_filters = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional filters for contact selection"
    )
    
    class Meta:
        verbose_name = "Campaign"
        verbose_name_plural = "Campaigns"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'scheduled_at']),
            models.Index(fields=['organization', 'is_active', 'status']),
            models.Index(fields=['status', 'scheduled_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.status})"
    
    def clean(self):
        """Validate campaign configuration."""
        super().clean()
        
        if self.status == 'SCHEDULED' and not self.scheduled_at:
            raise ValidationError("Scheduled campaigns must have a scheduled_at time.")
        
        if self.scheduled_at and self.scheduled_at <= timezone.now():
            if self.status == 'SCHEDULED':
                raise ValidationError("Scheduled time must be in the future.")
    
    def save(self, *args, **kwargs):
        # Run validation
        self.clean()
        
        # Handle Celery Beat scheduling
        if self.status == 'SCHEDULED' and self.scheduled_at:
            self._setup_periodic_task()
        elif self.periodic_task:
            self._cleanup_periodic_task()
        
        super().save(*args, **kwargs)
    
    def _setup_periodic_task(self):
        """Create or update the Celery Beat periodic task."""
        import json
        
        # Create crontab schedule for the scheduled time
        crontab, _ = CrontabSchedule.objects.get_or_create(
            minute=self.scheduled_at.minute,
            hour=self.scheduled_at.hour,
            day_of_month=self.scheduled_at.day,
            month_of_year=self.scheduled_at.month,
            day_of_week='*',
        )
        
        task_name = f'campaign-{self.id}-{self.scheduled_at.isoformat()}'
        
        if self.periodic_task:
            self.periodic_task.crontab = crontab
            self.periodic_task.args = json.dumps([str(self.id)])
            self.periodic_task.enabled = True
            self.periodic_task.one_off = True
            self.periodic_task.save()
        else:
            self.periodic_task = PeriodicTask.objects.create(
                name=task_name,
                task='campaigns.tasks.launch_campaign_task',
                crontab=crontab,
                args=json.dumps([str(self.id)]),
                enabled=True,
                one_off=True,  # Execute only once
            )
    
    def _cleanup_periodic_task(self):
        """Remove the Celery Beat periodic task."""
        if self.periodic_task:
            self.periodic_task.delete()
            self.periodic_task = None
    
    @property
    def open_rate(self):
        """Calculate open rate percentage."""
        if self.stats_delivered == 0:
            return 0.0
        return (self.stats_unique_opens / self.stats_delivered) * 100
    
    @property
    def click_rate(self):
        """Calculate click rate percentage."""
        if self.stats_delivered == 0:
            return 0.0
        return (self.stats_unique_clicks / self.stats_delivered) * 100
    
    @property
    def bounce_rate(self):
        """Calculate bounce rate percentage."""
        if self.stats_sent == 0:
            return 0.0
        return (self.stats_bounced / self.stats_sent) * 100
    
    @property
    def delivery_rate(self):
        """Calculate delivery rate percentage."""
        if self.stats_sent == 0:
            return 0.0
        return (self.stats_delivered / self.stats_sent) * 100
    
    def update_stats_from_logs(self):
        """
        Update inline statistics by aggregating from EmailDeliveryLog.
        Uses TruncHour/TruncDay for efficient aggregation.
        """
        from django.db.models import Count, Q
        from .email_tracking_models import EmailDeliveryLog
        
        # Get aggregated stats from delivery logs
        stats = EmailDeliveryLog.objects.filter(
            campaign=self
        ).aggregate(
            total_sent=Count('id', filter=Q(delivery_status__in=['SENT', 'DELIVERED', 'BOUNCED', 'COMPLAINED', 'OPENED', 'CLICKED'])),
            delivered=Count('id', filter=Q(delivery_status__in=['DELIVERED', 'OPENED', 'CLICKED'])),
            opened=Count('id', filter=Q(delivery_status__in=['OPENED', 'CLICKED'])),
            clicked=Count('id', filter=Q(delivery_status='CLICKED')),
            bounced=Count('id', filter=Q(delivery_status='BOUNCED')),
            complained=Count('id', filter=Q(delivery_status='COMPLAINED')),
            unsubscribed=Count('id', filter=Q(delivery_status='UNSUBSCRIBED')),
            failed=Count('id', filter=Q(delivery_status='FAILED')),
            unique_opens=Count('recipient_email', distinct=True, filter=Q(opened_at__isnull=False)),
            unique_clicks=Count('recipient_email', distinct=True, filter=Q(clicked_at__isnull=False)),
        )
        
        self.stats_sent = stats['total_sent'] or 0
        self.stats_delivered = stats['delivered'] or 0
        self.stats_opened = stats['opened'] or 0
        self.stats_clicked = stats['clicked'] or 0
        self.stats_bounced = stats['bounced'] or 0
        self.stats_complained = stats['complained'] or 0
        self.stats_unsubscribed = stats['unsubscribed'] or 0
        self.stats_failed = stats['failed'] or 0
        self.stats_unique_opens = stats['unique_opens'] or 0
        self.stats_unique_clicks = stats['unique_clicks'] or 0
        self.stats_updated_at = timezone.now()
        
        self.save(update_fields=[
            'stats_sent', 'stats_delivered', 'stats_opened', 'stats_clicked',
            'stats_bounced', 'stats_complained', 'stats_unsubscribed', 'stats_failed',
            'stats_unique_opens', 'stats_unique_clicks', 'stats_updated_at'
        ])
    
    def calculate_total_recipients(self):
        """Calculate total unique recipients from contact lists."""
        from .contact_models import Contact
        
        # Get unique active contacts across all lists
        recipient_count = Contact.objects.filter(
            lists__in=self.contact_lists.all(),
            status='ACTIVE',
            is_active=True,
            is_deleted=False
        ).distinct().count()
        
        self.stats_total_recipients = recipient_count
        self.save(update_fields=['stats_total_recipients'])
        
        return recipient_count
    
    def launch(self):
        """
        Launch the campaign (change status and start sending).
        """
        if self.status not in ['DRAFT', 'SCHEDULED', 'PAUSED']:
            raise ValidationError(f"Cannot launch campaign with status {self.status}")
        
        self.status = 'SENDING'
        self.started_at = timezone.now()
        self.calculate_total_recipients()
        self.save(update_fields=['status', 'started_at', 'stats_total_recipients'])
        
        # Trigger async sending task
        from ..tasks import launch_campaign_task
        launch_campaign_task.delay(str(self.id))
    
    def pause(self):
        """Pause a running campaign."""
        if self.status != 'SENDING':
            raise ValidationError("Can only pause a sending campaign")
        
        self.status = 'PAUSED'
        self.save(update_fields=['status'])
    
    def resume(self):
        """Resume a paused campaign."""
        if self.status != 'PAUSED':
            raise ValidationError("Can only resume a paused campaign")
        
        self.status = 'SENDING'
        self.save(update_fields=['status'])
        
        # Trigger async sending task to continue
        from ..tasks import launch_campaign_task
        launch_campaign_task.delay(str(self.id))
    
    def cancel(self):
        """Cancel a campaign."""
        if self.status in ['SENT', 'CANCELLED']:
            raise ValidationError(f"Cannot cancel campaign with status {self.status}")
        
        self.status = 'CANCELLED'
        self._cleanup_periodic_task()
        self.save(update_fields=['status'])
    
    def mark_completed(self):
        """Mark campaign as completed."""
        self.status = 'SENT'
        self.completed_at = timezone.now()
        self._cleanup_periodic_task()
        self.save(update_fields=['status', 'completed_at'])
    
    def mark_failed(self, error_message: str = ""):
        """Mark campaign as failed."""
        self.status = 'FAILED'
        self._cleanup_periodic_task()
        if error_message:
            if not self.segment_filters:
                self.segment_filters = {}
            self.segment_filters['_error'] = error_message
        self.save(update_fields=['status', 'segment_filters'])
    
    def duplicate(self, new_name: str = None):
        """
        Create a duplicate of this campaign.
        
        Args:
            new_name: Optional new name for the duplicate
            
        Returns:
            The new Campaign instance
        """
        # Create new instance with same data
        new_campaign = Campaign(
            organization=self.organization,
            name=new_name or f"{self.name} (Copy)",
            description=self.description,
            subject=self.subject,
            preview_text=self.preview_text,
            html_content=self.html_content,
            text_content=self.text_content,
            from_name=self.from_name,
            from_email=self.from_email,
            reply_to=self.reply_to,
            email_template=self.email_template,
            email_provider=self.email_provider,
            status='DRAFT',
            batch_size=self.batch_size,
            batch_delay_seconds=self.batch_delay_seconds,
            track_opens=self.track_opens,
            track_clicks=self.track_clicks,
            tags=self.tags.copy() if self.tags else [],
            segment_filters=self.segment_filters.copy() if self.segment_filters else None,
        )
        new_campaign.save()
        
        # Copy contact list associations
        new_campaign.contact_lists.set(self.contact_lists.all())
        
        return new_campaign
    
    def preview(self, contact=None):
        """
        Generate a preview of the campaign email.
        
        Args:
            contact: Optional Contact instance for personalization preview
            
        Returns:
            Dict with subject, html_content, text_content
        """
        subject = self.subject
        html_content = self.html_content
        text_content = self.text_content
        
        # Simple variable replacement for preview
        if contact:
            replacements = {
                '{{first_name}}': contact.first_name or '',
                '{{last_name}}': contact.last_name or '',
                '{{email}}': contact.email,
                '{{full_name}}': contact.full_name or contact.email,
            }
            
            # Add custom fields
            if contact.custom_fields:
                for key, value in contact.custom_fields.items():
                    replacements[f'{{{{{key}}}}}'] = str(value) if value else ''
            
            for placeholder, value in replacements.items():
                subject = subject.replace(placeholder, value)
                html_content = html_content.replace(placeholder, value)
                text_content = text_content.replace(placeholder, value)
        
        return {
            'subject': subject,
            'html_content': html_content,
            'text_content': text_content,
            'from_name': self.from_name,
            'from_email': self.from_email,
            'preview_text': self.preview_text,
        }
    
    def send_test(self, test_emails: list, contact=None):
        """
        Send a test email to specified addresses.
        
        Args:
            test_emails: List of email addresses to send test to
            contact: Optional Contact for personalization preview
            
        Returns:
            List of send results
        """
        from ..tasks import send_test_campaign_email
        
        preview = self.preview(contact)
        results = []
        
        for email in test_emails:
            result = send_test_campaign_email.delay(
                campaign_id=str(self.id),
                recipient_email=email,
                subject=f"[TEST] {preview['subject']}",
                html_content=preview['html_content'],
                text_content=preview['text_content'],
            )
            results.append({
                'email': email,
                'task_id': result.id
            })
        
        return results
