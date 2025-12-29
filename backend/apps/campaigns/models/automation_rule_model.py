"""
Automation rule model for triggering automated communications.
"""
import json
import uuid

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule

from .email_config_models import EmailTemplate
from .sms_config_models import SMSConfigurationModel, SMSTemplate
from .organization_email_config import OrganizationEmailConfiguration
from .provider_models import OrganizationEmailProvider, EmailProvider
from apps.utils.base_models import BaseModel
from apps.authentication.models import Organization


class AutomationRule(BaseModel):
    """
    Defines rules for triggering automated communications.
    Links to a PeriodicTask for scheduled rules.
    
    All rules are organization-scoped (no more GLOBAL/TENANT scope).
    """
    
    class ReasonName(models.TextChoices):
        # Transactional emails
        EMAIL_VERIFICATION = 'EMAIL_VERIFICATION', 'Email Verification'
        PASSWORD_RESET = 'PASSWORD_RESET', 'Password Reset'
        WELCOME_EMAIL = 'WELCOME_EMAIL', 'Welcome Email'
        
        # Campaign-related
        CAMPAIGN_LAUNCH = 'CAMPAIGN_LAUNCH', 'Campaign Launch'
        CAMPAIGN_REMINDER = 'CAMPAIGN_REMINDER', 'Campaign Reminder'
        CAMPAIGN_FOLLOWUP = 'CAMPAIGN_FOLLOWUP', 'Campaign Follow-up'
        
        # Subscription events
        SUBSCRIPTION_CONFIRMATION = 'SUBSCRIPTION_CONFIRMATION', 'Subscription Confirmation'
        SUBSCRIPTION_RENEWAL = 'SUBSCRIPTION_RENEWAL', 'Subscription Renewal'
        SUBSCRIPTION_EXPIRING = 'SUBSCRIPTION_EXPIRING', 'Subscription Expiring'
        
        # User events
        INVITATION_SENT = 'INVITATION_SENT', 'Invitation Sent'
        INVITATION_REMINDER = 'INVITATION_REMINDER', 'Invitation Reminder'
        MEMBER_ONBOARDING = 'MEMBER_ONBOARDING', 'Member Onboarding'
        
        # Custom/Other
        OTHER = 'OTHER', 'Other'

    class CommunicationType(models.TextChoices):
        EMAIL = 'EMAIL', 'Email'
        SMS = 'SMS', 'SMS'
        WHATSAPP = 'WHATSAPP', 'WhatsApp'
        PUSH = 'PUSH', 'Push Notification'

    class TriggerType(models.TextChoices):
        IMMEDIATE = 'IMMEDIATE', 'Immediate'
        DELAY = 'DELAY', 'Delay'
        SCHEDULE = 'SCHEDULE', 'Schedule'

    class DelayUnit(models.TextChoices):
        SECONDS = 'SECONDS', 'Seconds'
        MINUTES = 'MINUTES', 'Minutes'
        HOURS = 'HOURS', 'Hours'
        DAYS = 'DAYS', 'Days'
    
    class ScheduleFrequency(models.TextChoices):
        INTERVAL = 'INTERVAL', 'Interval'
        DAILY = 'DAILY', 'Daily'
        WEEKLY = 'WEEKLY', 'Weekly'
        MONTHLY = 'MONTHLY', 'Monthly'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    automation_name = models.CharField(max_length=100)
    
    # Organization ownership (all rules are org-scoped now)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='automation_rules',
        help_text="Organization this rule belongs to"
    )
    
    reason_name = models.CharField(max_length=100, choices=ReasonName.choices)
    action_name = models.CharField(max_length=100, blank=True)
    communication_type = models.CharField(max_length=10, choices=CommunicationType.choices, default=CommunicationType.EMAIL)
    short_description = models.TextField(blank=True, help_text="A brief description of the automation rule.")
   
    # Template references
    email_template = models.ForeignKey(
        EmailTemplate, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='automation_rules'
    )
    sms_template = models.ForeignKey(
        SMSTemplate, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='automation_rules'
    )
    
    # SMS configuration
    sms_config = models.ForeignKey(
        SMSConfigurationModel, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='automation_rules'
    )
    
    # Email configuration and provider
    email_config = models.ForeignKey(
        OrganizationEmailConfiguration, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='automation_rules'
    )
    email_provider = models.ForeignKey(
        OrganizationEmailProvider, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='automation_rules',
        help_text="Organization-specific provider configuration"
    )
    
    # Campaign and ContactList references (new)
    campaign = models.ForeignKey(
        'Campaign',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='automation_rules',
        help_text="Campaign to launch when this rule triggers"
    )
    contact_list = models.ForeignKey(
        'ContactList',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='automation_rules',
        help_text="Contact list to target when this rule triggers"
    )
    
    # --- Dynamic scheduling fields ---
    trigger_type = models.CharField(max_length=20, choices=TriggerType.choices, default=TriggerType.IMMEDIATE)
    
    # Fields for DELAY trigger
    delay_amount = models.PositiveIntegerField(null=True, blank=True, help_text="Amount of time to delay. (e.g., 5, 10, 20)")
    delay_unit = models.CharField(max_length=20, choices=DelayUnit.choices, null=True, blank=True, help_text="Unit of time for the delay (e.g., SECONDS, MINUTES, etc.).")
    
    # User-friendly fields for SCHEDULE trigger
    schedule_frequency = models.CharField(max_length=20, choices=ScheduleFrequency.choices, null=True, blank=True, help_text="Frequency of the schedule (e.g., INTERVAL, DAILY, WEEKLY, MONTHLY).")
    schedule_interval_amount = models.PositiveIntegerField(null=True, blank=True, help_text="e.g., every '5' minutes")
    schedule_interval_unit = models.CharField(max_length=20, choices=DelayUnit.choices, null=True, blank=True, help_text="e.g., every 5 'minutes'")
    schedule_time = models.TimeField(null=True, blank=True, help_text="Time of day to send (UTC). e.g., 2:30 PM UTC")
    schedule_day_of_week = models.PositiveIntegerField(null=True, blank=True, help_text="1=Monday, 7=Sunday")
    schedule_day_of_month = models.PositiveIntegerField(null=True, blank=True, help_text="1-31")
    num_occurrences = models.PositiveIntegerField(null=True, blank=True, help_text="Number of times to execute the scheduled task. Leave blank for indefinite.")

    # Enhanced configuration
    max_retries = models.PositiveIntegerField(default=3)
    retry_delay_minutes = models.PositiveIntegerField(default=5)
    batch_size = models.PositiveIntegerField(default=1, help_text="Number of emails to process in one batch")
    
    # Advanced filtering and conditions
    filter_conditions = models.JSONField(
        null=True, 
        blank=True, 
        help_text="JSON conditions for advanced filtering. Example: {'status': 'active', 'tags': ['premium']}"
    )
    
    # Status and metadata
    priority = models.PositiveIntegerField(default=5, help_text="1=highest priority, 10=lowest priority")

    # Link to the actual Celery Beat task
    periodic_task = models.OneToOneField(PeriodicTask, on_delete=models.SET_NULL, null=True, blank=True)

    def clean(self):
        """Validate rule configuration."""
        if self.trigger_type == self.TriggerType.DELAY:
            if not self.delay_amount or not self.delay_unit:
                raise ValidationError("Delay amount and unit are required for DELAY trigger type")
                
        if self.trigger_type == self.TriggerType.SCHEDULE:
            if not self.schedule_frequency:
                raise ValidationError("Schedule frequency is required for SCHEDULE trigger type")
        
        # Validate template matches communication type
        if self.communication_type == self.CommunicationType.EMAIL and not self.email_template:
            if not self.campaign:  # Campaign can have its own content
                raise ValidationError("Email template or campaign is required for EMAIL communication type")
        
        if self.communication_type == self.CommunicationType.SMS and not self.sms_template:
            raise ValidationError("SMS template is required for SMS communication type")

    def save(self, *args, **kwargs):
        # Run validation
        self.clean()

        # Automatically create/update the PeriodicTask when the rule is saved
        if self.trigger_type == self.TriggerType.SCHEDULE:
            self._setup_periodic_task()
        elif self.periodic_task:
            self._cleanup_periodic_task()

        super().save(*args, **kwargs)
    
    def _setup_periodic_task(self):
        """Create or update the Celery Beat periodic task."""
        # Choose task based on communication type
        if self.communication_type == self.CommunicationType.EMAIL:
            task_name = 'campaigns.tasks.dispatch_scheduled_email_task'
        elif self.communication_type == self.CommunicationType.SMS:
            task_name = 'campaigns.tasks.dispatch_scheduled_sms_task'
        else:
            task_name = 'campaigns.tasks.dispatch_scheduled_notification_task'
            
        task_args = json.dumps([str(self.id)])

        # Prepare defaults for the periodic task
        defaults = {'task': task_name, 'args': task_args}

        if self.schedule_frequency == self.ScheduleFrequency.INTERVAL:
            schedule, _ = IntervalSchedule.objects.get_or_create(
                every=self.schedule_interval_amount,
                period=self.schedule_interval_unit.lower()[:-1] if self.schedule_interval_unit else 'minutes',
            )
            defaults['interval'] = schedule
            defaults['crontab'] = None
        else:
            crontab_data = {
                'minute': self.schedule_time.minute if self.schedule_time else 0,
                'hour': self.schedule_time.hour if self.schedule_time else 0,
                'day_of_week': '*' if self.schedule_frequency != self.ScheduleFrequency.WEEKLY else str(self.schedule_day_of_week or 1),
                'day_of_month': '*' if self.schedule_frequency != self.ScheduleFrequency.MONTHLY else str(self.schedule_day_of_month or 1),
                'month_of_year': '*',
            }
            schedule, _ = CrontabSchedule.objects.get_or_create(**crontab_data)
            defaults['crontab'] = schedule
            defaults['interval'] = None

        # Create or update the periodic task
        if self.periodic_task:
            PeriodicTask.objects.filter(id=self.periodic_task.id).update(**defaults)
            self.periodic_task.refresh_from_db()
        else:
            self.periodic_task = PeriodicTask.objects.create(
                name=f'Rule-{self.automation_name}-{self.id or timezone.now()}',
                **defaults
            )
        
        self.periodic_task.enabled = self.is_active
        self.periodic_task.save()
    
    def _cleanup_periodic_task(self):
        """Remove the Celery Beat periodic task."""
        if self.periodic_task:
            self.periodic_task.delete()
            self.periodic_task = None

    def get_effective_email_provider(self):
        """
        Get the effective email provider for this rule.
        
        Returns:
            OrganizationEmailProvider or None
        """
        # Priority 1: Explicit provider on rule
        if self.email_provider and self.email_provider.is_enabled:
            return self.email_provider
        
        # Priority 2: Organization's primary provider
        return OrganizationEmailProvider.objects.filter(
            organization=self.organization,
            is_enabled=True,
            is_primary=True
        ).first()
    
    def get_effective_config(self):
        """Get the effective email configuration for this rule."""
        if self.email_config:
            return self.email_config
        
        # Fallback to organization's config
        config, _ = OrganizationEmailConfiguration.objects.get_or_create(
            organization=self.organization,
            defaults={'plan_type': 'FREE'}
        )
        return config

    class Meta:
        constraints = [
            # Only one rule per reason_name + communication_type per organization
            models.UniqueConstraint(
                fields=['organization', 'reason_name', 'communication_type'],
                condition=models.Q(is_deleted=False),
                name='unique_org_automation_rule'
            ),
        ]
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['reason_name', 'communication_type']),
            models.Index(fields=['trigger_type', 'is_active']),
            models.Index(fields=['campaign', 'is_active']),
        ]
        verbose_name = "Automation Rule"
        verbose_name_plural = "Automation Rules"

    def __str__(self):
        return f"{self.automation_name} ({self.organization.name})"
