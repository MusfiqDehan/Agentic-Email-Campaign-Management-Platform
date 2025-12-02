"""
Organization-specific email configuration and limits.
"""
import uuid
import threading
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from datetime import timezone as dt_timezone
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.utils.base_models import BaseModel
from apps.authentication.models import Organization
from decouple import config
from ..constants import get_plan_limits, get_default_plan_limits_json, COMMON_TIMEZONE_CHOICES


# Thread-local storage to prevent recursion
_thread_locals = threading.local()


def _get_recursion_guard(key):
    """Get recursion guard for current thread"""
    if not hasattr(_thread_locals, 'recursion_guards'):
        _thread_locals.recursion_guards = {}
    return _thread_locals.recursion_guards.get(key, False)


def _set_recursion_guard(key, value):
    """Set recursion guard for current thread"""
    if not hasattr(_thread_locals, 'recursion_guards'):
        _thread_locals.recursion_guards = {}
    _thread_locals.recursion_guards[key] = value


class OrganizationEmailConfiguration(BaseModel):
    """
    Organization-specific email configuration and limits.
    
    Each organization has one configuration that controls:
    - Plan type and associated limits
    - Custom domain settings
    - Usage tracking
    - Reputation metrics
    """
    
    PLAN_TYPES = [
        ('FREE', 'Free'),
        ('BASIC', 'Basic'),
        ('PROFESSIONAL', 'Professional'),
        ('ENTERPRISE', 'Enterprise'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.OneToOneField(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='email_configuration'
    )
    
    # Timezone for the organization (for scheduling campaigns)
    timezone = models.CharField(
        max_length=50, 
        default='UTC',
        help_text="Organization timezone for campaign scheduling"
    )
    
    # Subscription plan (can be synced from billing service or set manually)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default='FREE')
    
    # Plan limits (JSONField for flexibility, initialized from constants)
    plan_limits = models.JSONField(
        default=get_default_plan_limits_json,
        help_text="Plan limits including batch_size, api_requests_per_minute, etc."
    )
    
    # Email limits based on plan (denormalized for quick access)
    emails_per_day = models.PositiveIntegerField(default=100)
    emails_per_month = models.PositiveIntegerField(default=1000)
    emails_per_minute = models.PositiveIntegerField(default=10)
    
    # Email domain configuration
    default_from_domain = models.CharField(max_length=255, null=True, blank=True)
    custom_domain = models.CharField(max_length=255, null=True, blank=True)
    custom_domain_verified = models.BooleanField(default=False)
    domain_verification_token = models.CharField(max_length=255, blank=True)
    
    # Current usage tracking (reset daily/monthly by background tasks)
    emails_sent_today = models.PositiveIntegerField(default=0)
    emails_sent_this_month = models.PositiveIntegerField(default=0)
    last_email_sent_at = models.DateTimeField(null=True, blank=True)
    last_daily_reset = models.DateField(null=True, blank=True)
    last_monthly_reset = models.DateField(null=True, blank=True)
    
    # API usage tracking
    api_requests_today = models.PositiveIntegerField(default=0)
    last_api_request_at = models.DateTimeField(null=True, blank=True)
    
    # Status and suspension
    is_suspended = models.BooleanField(default=False)
    suspension_reason = models.TextField(blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    
    # Email reputation and health
    bounce_rate = models.FloatField(default=0.0, help_text="Bounce rate percentage")
    complaint_rate = models.FloatField(default=0.0, help_text="Complaint rate percentage")
    reputation_score = models.FloatField(default=100.0, help_text="Email reputation score (0-100)")
    
    def clean(self):
        """Validate configuration."""
        super().clean()
        
        # Validate timezone
        if self.timezone:
            try:
                ZoneInfo(self.timezone)
            except (ZoneInfoNotFoundError, KeyError):
                raise ValidationError(f"Invalid timezone: {self.timezone}")
    
    def save(self, *args, **kwargs):
        # Validate before save
        self.clean()
        
        # Sync plan limits from plan_type if plan changed
        if self.pk:
            try:
                old = OrganizationEmailConfiguration.objects.get(pk=self.pk)
                if old.plan_type != self.plan_type:
                    self.sync_plan_limits()
            except OrganizationEmailConfiguration.DoesNotExist:
                self.sync_plan_limits()
        else:
            self.sync_plan_limits()
        
        super().save(*args, **kwargs)
    
    def sync_plan_limits(self):
        """Sync limits from plan_type to plan_limits and denormalized fields."""
        limits = get_plan_limits(self.plan_type)
        self.plan_limits = limits
        self.emails_per_day = limits.get('emails_per_day', 100)
        self.emails_per_month = limits.get('emails_per_month', 1000)
        self.emails_per_minute = limits.get('emails_per_minute', 10)
    
    def _ensure_counters_current(self):
        """
        Ensure daily/monthly counters are reset if date has changed.
        This prevents stale counter checks.
        """
        # Prevent recursion using thread-local guard
        guard_key = f'updating_counters_{self.organization_id}'
        if _get_recursion_guard(guard_key):
            return
        
        today = timezone.now().date()
        needs_save = False
        
        # Reset daily counter if needed
        if self.last_daily_reset != today:
            self.emails_sent_today = 0
            self.api_requests_today = 0
            self.last_daily_reset = today
            needs_save = True
            
        # Reset monthly counter if needed  
        if not self.last_monthly_reset or self.last_monthly_reset.month != today.month:
            self.emails_sent_this_month = 0
            self.last_monthly_reset = today
            needs_save = True
        
        if needs_save:
            try:
                _set_recursion_guard(guard_key, True)
                self.save(update_fields=[
                    'emails_sent_today', 'emails_sent_this_month', 
                    'api_requests_today', 'last_daily_reset', 'last_monthly_reset'
                ])
            finally:
                _set_recursion_guard(guard_key, False)
    
    def can_send_email(self, check_provider_limits=True, provider=None):
        """
        Check if organization can send email based on limits and status.
        
        Args:
            check_provider_limits: If True, also check provider-level rate limits
            provider: OrganizationEmailProvider instance (for checking provider limits)
            
        Returns:
            Tuple of (can_send: bool, reason: str)
        """
        # Prevent recursion using thread-local guard
        guard_key = f'checking_send_{self.organization_id}'
        if _get_recursion_guard(guard_key):
            return True, "OK (recursion guard)"
        
        try:
            _set_recursion_guard(guard_key, True)
            
            # Ensure counters are current before checking limits
            self._ensure_counters_current()
            
            if not self.is_active or self.is_suspended:
                return False, "Organization email service is not active or suspended"
                
            if self.emails_sent_today >= self.emails_per_day:
                return False, "Daily email limit exceeded"
                
            if self.emails_sent_this_month >= self.emails_per_month:
                return False, "Monthly email limit exceeded"
                
            # Check reputation thresholds
            if self.bounce_rate > 10.0:  # 10% bounce rate threshold
                return False, "High bounce rate detected"
                
            if self.complaint_rate > 0.5:  # 0.5% complaint rate threshold
                return False, "High complaint rate detected"
            
            # Check provider-level limits if requested
            if check_provider_limits and provider:
                can_send, reason = provider.can_send_email()
                if not can_send:
                    return False, reason
                
            return True, "OK"
        finally:
            _set_recursion_guard(guard_key, False)
    
    def can_make_api_request(self):
        """
        Check if organization can make an API request based on rate limits.
        
        Returns:
            Tuple of (can_request: bool, reason: str)
        """
        self._ensure_counters_current()
        
        if not self.is_active or self.is_suspended:
            return False, "Organization is not active or suspended"
        
        api_limit = self.plan_limits.get('api_requests_per_minute', 60)
        # For simplicity, we check daily limit; per-minute should use Redis
        if self.api_requests_today >= api_limit * 60 * 24:  # Rough daily estimate
            return False, "API rate limit exceeded"
        
        return True, "OK"
    
    def increment_email_usage(self):
        """Increment email usage counters."""
        self._ensure_counters_current()
        
        self.emails_sent_today += 1
        self.emails_sent_this_month += 1
        self.last_email_sent_at = timezone.now()
        self.save(update_fields=['emails_sent_today', 'emails_sent_this_month', 'last_email_sent_at'])
    
    def increment_api_usage(self):
        """Increment API usage counter."""
        self._ensure_counters_current()
        
        self.api_requests_today += 1
        self.last_api_request_at = timezone.now()
        self.save(update_fields=['api_requests_today', 'last_api_request_at'])
    
    def get_effective_from_domain(self):
        """Get the effective from domain (custom or default)."""
        if self.is_custom_domain_allowed and self.custom_domain and self.custom_domain_verified:
            return self.custom_domain
        return self.default_from_domain or config('DEFAULT_ORG_DOMAIN', default='')
    
    @property
    def is_custom_domain_allowed(self):
        """Check if custom domain is allowed for this plan."""
        return self.plan_limits.get('custom_domain_allowed', False)
    
    @property
    def is_bulk_email_allowed(self):
        """Check if bulk email is allowed for this plan."""
        return self.plan_limits.get('bulk_email_allowed', False)
    
    @property
    def batch_size(self):
        """Get the batch size for this organization's plan."""
        return self.plan_limits.get('batch_size', 100)
    
    @property
    def contacts_limit(self):
        """Get the contacts limit for this organization's plan."""
        return self.plan_limits.get('contacts_limit')
    
    @property
    def campaigns_per_month(self):
        """Get the campaigns per month limit for this organization's plan."""
        return self.plan_limits.get('campaigns_per_month')
    
    def get_daily_limit(self):
        """Get the daily email limit for this organization."""
        return self.emails_per_day
    
    def get_monthly_limit(self):
        """Get the monthly email limit for this organization."""
        return self.emails_per_month
    
    def convert_to_org_timezone(self, utc_datetime):
        """
        Convert a UTC datetime to the organization's timezone.
        
        Args:
            utc_datetime: A datetime object in UTC
            
        Returns:
            Datetime in the organization's timezone
        """
        if utc_datetime is None:
            return None
        
        org_tz = ZoneInfo(self.timezone)
        if utc_datetime.tzinfo is None:
            utc_datetime = utc_datetime.replace(tzinfo=dt_timezone.utc)
        return utc_datetime.astimezone(org_tz)
    
    def convert_to_utc(self, local_datetime):
        """
        Convert a datetime in the organization's timezone to UTC.
        
        Args:
            local_datetime: A datetime object in the organization's timezone
            
        Returns:
            Datetime in UTC
        """
        if local_datetime is None:
            return None
        
        org_tz = ZoneInfo(self.timezone)
        if local_datetime.tzinfo is None:
            local_datetime = local_datetime.replace(tzinfo=org_tz)
        return local_datetime.astimezone(dt_timezone.utc)
    
    class Meta:
        verbose_name = "Organization Email Configuration"
        verbose_name_plural = "Organization Email Configurations"
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['plan_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"Email Config for {self.organization.name} ({self.plan_type})"


# Legacy alias for backward compatibility during migration
TenantEmailConfiguration = OrganizationEmailConfiguration
