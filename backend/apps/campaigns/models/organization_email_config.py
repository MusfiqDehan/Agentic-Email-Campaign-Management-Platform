"""
Organization-specific email configuration and limits.
"""
import uuid
import threading
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from datetime import timezone as dt_timezone
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.utils.base_models import BaseModel
from apps.authentication.models import Organization
from decouple import config
from ..constants import get_plan_limits, get_default_plan_limits_json, COMMON_TIMEZONE_CHOICES
from .package_models import STARTER_PACKAGE_SLUGS, STARTER_PLAN_TYPES


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
        ('TRIAL', 'Trial'),
        ('BASIC', 'Basic'),
        ('PROFESSIONAL', 'Professional'),
        ('ENTERPRISE', 'Enterprise'),
    ]

    _USAGE_FIELDS = (
        'emails_sent_today', 'emails_sent_this_month', 'api_requests_today',
        'last_daily_reset', 'last_monthly_reset',
        'last_email_sent_at', 'last_api_request_at',
    )
    
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
    
    # Subscription plan (display mirror of package.name when a package is set)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default='FREE')

    # Plan limits (JSONField for flexibility, initialized from constants).
    # Legacy: authoritative only when `package` is NULL — see get_effective_limits().
    plan_limits = models.JSONField(
        default=get_default_plan_limits_json,
        help_text="Plan limits including batch_size, api_requests_per_minute, etc."
    )

    # DB-backed package assignment (platform-admin controlled). When set, it is
    # the authoritative source of limits/flags, refined by limit_overrides.
    package = models.ForeignKey(
        'campaigns.Package',
        null=True, blank=True,
        on_delete=models.PROTECT,
        related_name='organizations',
    )
    limit_overrides = models.JSONField(
        default=dict, blank=True,
        help_text="Sparse per-organization overrides of package limits/flags (override wins)"
    )
    domain_feature_enabled = models.BooleanField(
        default=True,
        help_text="Platform-admin kill switch for the sending-domains feature"
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
    
    # Sentinel used when a NULL (= unlimited) limit must fit a non-null
    # denormalized PositiveIntegerField.
    UNLIMITED_SENTINEL = 10 ** 9

    def save(self, *args, **kwargs):
        # Validate before save
        self.clean()

        if self.package_id:
            # Package is authoritative: keep plan_type as a display mirror and
            # refresh the denormalized counters from effective limits. Manual
            # limit_overrides always survive (they participate in the merge).
            mirrored = self.package.name.upper()
            if mirrored in dict(self.PLAN_TYPES):
                self.plan_type = mirrored
            self.sync_plan_limits()
        else:
            # Legacy path: sync from the hardcoded catalog only when the plan
            # type changes (or on first save).
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

    def get_effective_limits(self):
        """
        Effective limits/flags for this organization.

        Package limits merged with sparse per-org limit_overrides (override
        wins); falls back to the legacy plan_limits JSON when no package is
        assigned. NULL integer limits mean unlimited.
        """
        if self.package_id:
            limits = self.package.get_limits_dict()
        else:
            limits = dict(self.plan_limits or get_plan_limits(self.plan_type))
        overrides = self.limit_overrides or {}
        limits.update({k: v for k, v in overrides.items()})
        return limits

    def sync_plan_limits(self):
        """Refresh the denormalized limit fields (and legacy plan_limits JSON)."""
        if self.package_id:
            limits = self.get_effective_limits()
        else:
            limits = get_plan_limits(self.plan_type)
            self.plan_limits = limits

        def _num(value):
            # NULL limit = unlimited; denormalized fields are non-null ints
            return self.UNLIMITED_SENTINEL if value is None else value

        self.emails_per_day = _num(limits.get('emails_per_day', 100))
        self.emails_per_month = _num(limits.get('emails_per_month', 1000))
        self.emails_per_minute = _num(limits.get('emails_per_minute', 10))
    
    def _period_changed(self, today=None):
        """Whether daily and/or monthly counters need a calendar reset."""
        today = today or timezone.now().date()
        daily = self.last_daily_reset != today
        monthly = (
            not self.last_monthly_reset
            or self.last_monthly_reset.month != today.month
            or self.last_monthly_reset.year != today.year
        )
        return today, daily, monthly

    def _apply_counter_resets(self, today=None):
        """
        Mutate in-memory counters if the calendar period changed.

        Caller MUST hold a row lock (select_for_update) so a concurrent
        increment cannot be clobbered by a stale reset.
        """
        today, daily, monthly = self._period_changed(today)
        if daily:
            self.emails_sent_today = 0
            self.api_requests_today = 0
            self.last_daily_reset = today
        if monthly:
            self.emails_sent_this_month = 0
            self.last_monthly_reset = today
        return daily or monthly

    def _persist_usage_fields(self, extra_fields=()):
        """Write usage columns via QuerySet.update to skip save() hooks."""
        fields = set(self._USAGE_FIELDS) | set(extra_fields)
        payload = {field: getattr(self, field) for field in fields}
        payload['updated_at'] = timezone.now()
        type(self).objects.filter(pk=self.pk).update(**payload)

    def _lock_self(self):
        return type(self).objects.select_for_update().get(pk=self.pk)

    def _copy_usage_from(self, locked):
        for field in self._USAGE_FIELDS:
            setattr(self, field, getattr(locked, field))

    def _ensure_counters_current(self):
        """
        Ensure daily/monthly counters are reset if date has changed.

        Takes a row lock so a concurrent increment cannot be wiped by a
        late reset, and so two workers cannot both reset-and-write 0.
        """
        guard_key = f'updating_counters_{self.organization_id}'
        if _get_recursion_guard(guard_key):
            return

        if not self.pk:
            self._apply_counter_resets()
            return

        try:
            _set_recursion_guard(guard_key, True)
            with transaction.atomic():
                locked = self._lock_self()
                if locked._apply_counter_resets():
                    locked._persist_usage_fields()
                self._copy_usage_from(locked)
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
        guard_key = f'checking_send_{self.organization_id}'
        if _get_recursion_guard(guard_key):
            return True, "OK (recursion guard)"

        try:
            _set_recursion_guard(guard_key, True)

            self._ensure_counters_current()

            if not self.is_active or self.is_suspended:
                return False, "Organization email service is not active or suspended"

            if self.emails_sent_today >= self.emails_per_day:
                return False, "Daily email limit exceeded"

            if self.emails_sent_this_month >= self.emails_per_month:
                return False, "Monthly email limit exceeded"

            if self.bounce_rate > 10.0:
                return False, "High bounce rate detected"

            if self.complaint_rate > 0.5:
                return False, "High complaint rate detected"

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
        
        api_limit = self.get_effective_limits().get('api_requests_per_minute', 60) or 60
        # For simplicity, we check daily limit; per-minute should use Redis
        if self.api_requests_today >= api_limit * 60 * 24:  # Rough daily estimate
            return False, "API rate limit exceeded"
        
        return True, "OK"
    
    def increment_email_usage(self, count=1):
        """
        Atomically increment email usage counters.

        Resets and the increment happen under one row lock so concurrent
        workers cannot lose updates or wipe a just-incremented daily count
        with a stale period reset.
        """
        if count <= 0 or not self.pk:
            return

        with transaction.atomic():
            locked = self._lock_self()
            locked._apply_counter_resets()
            locked.emails_sent_today += count
            locked.emails_sent_this_month += count
            locked.last_email_sent_at = timezone.now()
            locked._persist_usage_fields()
            self._copy_usage_from(locked)

    def increment_api_usage(self, count=1):
        """Atomically increment the API usage counter under a row lock."""
        if count <= 0 or not self.pk:
            return

        with transaction.atomic():
            locked = self._lock_self()
            locked._apply_counter_resets()
            locked.api_requests_today += count
            locked.last_api_request_at = timezone.now()
            locked._persist_usage_fields()
            self._copy_usage_from(locked)

    @property
    def is_starter_plan(self):
        """True when this org is on a free/trial package (or legacy FREE/TRIAL)."""
        if self.package_id:
            return (self.package.name or '').lower() in STARTER_PACKAGE_SLUGS
        return (self.plan_type or 'FREE').upper() in STARTER_PLAN_TYPES
    
    def get_effective_from_domain(self):
        """Get the effective from domain (custom or default)."""
        if self.is_custom_domain_allowed and self.custom_domain and self.custom_domain_verified:
            return self.custom_domain
        return self.default_from_domain or config('DEFAULT_ORG_DOMAIN', default='')
    
    @property
    def is_custom_domain_allowed(self):
        """Check if custom domain is allowed for this plan."""
        return bool(self.get_effective_limits().get('custom_domain_allowed', False))

    @property
    def is_bulk_email_allowed(self):
        """Check if bulk email is allowed for this plan."""
        return bool(self.get_effective_limits().get('bulk_email_allowed', False))

    @property
    def is_org_owned_ses_allowed(self):
        """Check if org-owned SES domains are allowed for this plan."""
        return bool(self.get_effective_limits().get('org_owned_ses_allowed', False))

    @property
    def batch_size(self):
        """Get the batch size for this organization's plan."""
        return self.get_effective_limits().get('batch_size') or 100

    @property
    def contacts_limit(self):
        """Get the contacts limit for this organization's plan."""
        return self.get_effective_limits().get('contacts_limit')

    @property
    def campaigns_per_month(self):
        """Get the campaigns per month limit for this organization's plan."""
        return self.get_effective_limits().get('campaigns_per_month')

    @property
    def max_domains(self):
        """Max sending domains for this organization (None = unlimited)."""
        return self.get_effective_limits().get('max_domains', 0)

    @property
    def max_sender_emails(self):
        """Max sender email addresses for this organization (None = unlimited)."""
        return self.get_effective_limits().get('max_sender_emails', 0)
    
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
