import json
import uuid

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule

from .email_config_models import EmailTemplate
from .sms_config_models import SMSConfigurationModel, SMSTemplate
from .tenant_email_config import TenantEmailConfiguration
from .provider_models import TenantEmailProvider
from utils.base_models import BaseModel
from authentication.models import Organization


class AutomationRule(BaseModel):
    """
    Defines rules for triggering automated communications.
    Links to a PeriodicTask for scheduled rules.

    Attributes:
        automation_name (str): Unique name for the automation rule.
        product_id (UUIDField): Optional product ID to associate with this rule.
        reason_name (str): Name of the reason for triggering this rule.
        action_name (str): Name of the action to be taken.
        communication_type (str): Type of communication (EMAIL, SMS, etc.).
        short_description (str): Brief description of the automation rule.
        email_template_id (ForeignKey): Link to the EmailTemplate for EMAIL communication.
        sms_template_id (ForeignKey): Link to the SMSTemplate for SMS communication.
        sms_config_id (ForeignKey): Link to the SMSConfigurationModel for SMS communication.
        tenant_email_config (ForeignKey): Link to the TenantEmailConfiguration for tenant-specific email settings.
        preferred_email_provider (ForeignKey): Link to TenantEmailProvider for tenant-scoped rules.
        preferred_global_provider (ForeignKey): Link to EmailProvider for global rules or direct provider selection.
        trigger_type (str): Type of trigger (IMMEDIATE, DELAY, SCHEDULE).
        delay_amount (int): Amount of time to delay for DELAY trigger.
        delay_unit (str): Unit of time for the delay (SECONDS, MINUTES, etc.).
        schedule_frequency (str): Frequency of the schedule (INTERVAL, DAILY, WEEKLY, MONTHLY).
        schedule_interval_amount (int): Amount for INTERVAL frequency.
        schedule_interval_unit (str): Unit for INTERVAL frequency (SECONDS, MINUTES, etc.).
        schedule_time (TimeField): Time of day to send for DAILY, WEEKLY, or MONTHLY frequency.
        schedule_day_of_week (int): Day of the week for WEEKLY frequency (1=Monday, 7=Sunday).
        schedule_day_of_month (int): Day of the month for MONTHLY frequency (1-31).
        periodic_task (OneToOneField):
            Link to the actual Celery Beat task that executes this rule.
        
    Meta:
        verbose_name_plural (str): The plural name for the model in the admin interface.
        unique_together (tuple): Ensure unique combination of automation_name and product_id.
    """
    class ReasonName(models.TextChoices):
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
    
    class RuleScope(models.TextChoices):
        TENANT = 'TENANT', 'Tenant Specific'
        GLOBAL = 'GLOBAL', 'Global Organization'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    automation_name = models.CharField(max_length=100)
    org_id = models.ForeignKey(Organization, on_delete=models.CASCADE, help_text="Organization this rule belongs to")
    rule_scope = models.CharField(max_length=10, choices=RuleScope.choices, default=RuleScope.TENANT, help_text="Whether this rule applies to a specific tenant or globally")
    product_id = models.UUIDField(blank=True, null=True, db_index=True, help_text="Optional product ID for filtering")
    reason_name = models.CharField(max_length=100, choices=ReasonName.choices)
    action_name = models.CharField(max_length=100, blank=True)
    communication_type = models.CharField(max_length=10, choices=CommunicationType.choices, default=CommunicationType.EMAIL)
    short_description = models.TextField(blank=True, help_text="A brief description of the automation rule.")
   
    # Enhanced template fields with better relationships
    email_template_id = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE, null=True, blank=True)
    sms_template_id = models.ForeignKey(SMSTemplate, on_delete=models.CASCADE, null=True, blank=True)
    
    # SMS configuration
    sms_config_id = models.ForeignKey(SMSConfigurationModel, on_delete=models.CASCADE, null=True, blank=True)
    
    # Enhanced configuration fields for email
    tenant_email_config = models.ForeignKey(TenantEmailConfiguration, on_delete=models.CASCADE, null=True, blank=True)
    preferred_email_provider = models.ForeignKey(
        TenantEmailProvider, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Tenant-specific provider configuration (for tenant-scoped rules)"
    )
    preferred_global_provider = models.ForeignKey(
        'EmailProvider',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='automation_rules_using',
        help_text="Global provider (for global rules or direct provider selection)"
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
        help_text="JSON conditions for advanced filtering. Example: {'user_status': 'active', 'plan_type': ['premium', 'enterprise']}"
    )
    
    # Status and metadata
    priority = models.PositiveIntegerField(default=5, help_text="1=highest priority, 10=lowest priority")

    # Link to the actual Celery Beat task
    periodic_task = models.OneToOneField(PeriodicTask, on_delete=models.SET_NULL, null=True, blank=True)


    def clean(self):
        """Validate rule configuration"""
            
        if self.trigger_type == self.TriggerType.DELAY:
            if not self.delay_amount or not self.delay_unit:
                raise ValidationError("Delay amount and unit are required for DELAY trigger type")
                
        if self.trigger_type == self.TriggerType.SCHEDULE:
            if not self.schedule_frequency:
                raise ValidationError("Schedule frequency is required for SCHEDULE trigger type")

    def save(self, *args, **kwargs):
        # Run validation
        self.clean()

        # Automatically create/update the PeriodicTask when the rule is saved
        if self.trigger_type == self.TriggerType.SCHEDULE:
            # Choose task based on communication type
            if self.communication_type == self.CommunicationType.EMAIL:
                task_name = 'automation_rule.tasks.dispatch_scheduled_email_task'
            elif self.communication_type == self.CommunicationType.SMS:
                task_name = 'automation_rule.tasks.dispatch_scheduled_sms_task'
            else:
                task_name = 'automation_rule.tasks.dispatch_scheduled_whatsapp_task'
                
            task_args = json.dumps([self.id])

            # Prepare defaults for the periodic task
            defaults = {'task': task_name, 'args': task_args}

            if self.schedule_frequency == self.ScheduleFrequency.INTERVAL:
                schedule, _ = IntervalSchedule.objects.get_or_create(
                    every=self.schedule_interval_amount,
                    period=self.schedule_interval_unit.lower()[:-1],
                )
                defaults['interval'] = schedule
                defaults['crontab'] = None # Ensure crontab is cleared
            else:
                crontab_data = {
                    'minute': self.schedule_time.minute,
                    'hour': self.schedule_time.hour,
                    'day_of_week': '*' if self.schedule_frequency != self.ScheduleFrequency.WEEKLY else self.schedule_day_of_week,
                    'day_of_month': '*' if self.schedule_frequency != self.ScheduleFrequency.MONTHLY else self.schedule_day_of_month,
                    'month_of_year': '*',
                }
                schedule, _ = CrontabSchedule.objects.get_or_create(**crontab_data)
                defaults['crontab'] = schedule
                defaults['interval'] = None # Ensure interval is cleared

            # Create or update the periodic task
            if self.periodic_task:
                # Update existing task
                PeriodicTask.objects.filter(id=self.periodic_task.id).update(**defaults)
                self.periodic_task.refresh_from_db()
            else:
                # Create new task
                self.periodic_task = PeriodicTask.objects.create(
                    name=f'Rule-{self.automation_name}-{self.id or timezone.now()}',
                    **defaults
                )
            
            self.periodic_task.enabled = True
            self.periodic_task.save()

        elif self.periodic_task:
            self.periodic_task.delete()
            self.periodic_task = None

        super().save(*args, **kwargs)

    def get_effective_email_provider(self):
        """
        Get the effective email provider for this rule.
        
        Priority:
        1. Tenant-specific provider (TenantEmailProvider) - for tenant rules
        2. Global provider (EmailProvider) - for global rules or direct selection
        3. Tenant's primary provider - fallback for tenant rules
        
        Returns:
            TenantEmailProvider or None
        """
        # Priority 1: Explicit tenant-specific provider
        if self.preferred_email_provider and self.preferred_email_provider.is_enabled:
            return self.preferred_email_provider
        
        # Priority 2: Global provider (wrap in TenantEmailProvider if tenant exists)
        if self.preferred_global_provider:
            # For global rules (no tenant), we need to handle this differently
            # The caller should use preferred_global_provider directly
            if not self.tenant_id:
                # Return None here, caller will check preferred_global_provider
                return None
            
            # For tenant rules, try to find or create TenantEmailProvider
            from .provider_models import TenantEmailProvider
            tenant_provider = TenantEmailProvider.objects.filter(
                tenant_id=self.tenant_id,
                provider=self.preferred_global_provider,
                is_enabled=True
            ).first()
            
            if tenant_provider:
                return tenant_provider
        
        # Priority 3: Tenant's primary provider (fallback)
        if self.tenant_id:
            from .provider_models import TenantEmailProvider
            return TenantEmailProvider.objects.filter(
                tenant_id=self.tenant_id,
                is_enabled=True,
                is_primary=True
            ).first()
        
        return None
    
    def get_effective_config(self):
        """Get the effective email configuration for this rule"""
        if self.tenant_email_config:
            return self.tenant_email_config
        
        # Fallback to getting or creating default config for tenant scoped rules only
        from .tenant_email_config import TenantEmailConfiguration

        if not self.tenant_id:
            # Global rules may not be tied to a tenant configuration.
            # Caller should handle the None case and provide a suitable fallback.
            return None

        config, _ = TenantEmailConfiguration.objects.get_or_create(
            tenant_id=self.tenant_id,
            defaults={
                'plan_type': 'FREE',
                'activated_by_tmd': True
            }
        )
        return config

    class Meta:
        constraints = [
            # Tenant-specific: Only one rule per reason_name + communication_type per tenant
            models.UniqueConstraint(
                fields=['tenant_id', 'reason_name', 'communication_type'],
                condition=models.Q(rule_scope='TENANT', is_deleted=False),
                name='unique_tenant_automation_rule'
            ),
            # Global: Only one rule per reason_name + communication_type globally
            models.UniqueConstraint(
                fields=['reason_name', 'communication_type'],
                condition=models.Q(rule_scope='GLOBAL', is_deleted=False),
                name='unique_global_automation_rule'
            ),
        ]
        indexes = [
            models.Index(fields=['tenant_id', 'activated_by_tmd']),
            models.Index(fields=['rule_scope', 'activated_by_tmd']),
            models.Index(fields=['reason_name', 'communication_type']),
            models.Index(fields=['product_id', 'activated_by_tmd']),
            models.Index(fields=['trigger_type', 'activated_by_tmd']),
        ]
        verbose_name = "Automation Rule"
        verbose_name_plural = "Automation Rules"

    def __str__(self):
        return self.automation_name