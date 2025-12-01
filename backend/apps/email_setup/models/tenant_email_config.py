import uuid
import threading
from django.db import models
from django.utils import timezone
from core import BaseModel
from decouple import config


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


class TenantEmailConfiguration(BaseModel):
    """Tenant-specific email configuration and limits"""
    
    PLAN_TYPES = [
        ('FREE', 'Free'),
        ('BASIC', 'Basic'),
        ('PROFESSIONAL', 'Professional'),
        ('ENTERPRISE', 'Enterprise'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(unique=True, db_index=True, help_text="Reference to tenant from tenant microservice")
    
    # Subscription plan (can be synced from billing service or set manually)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default='FREE')
    
    # Email limits based on plan
    emails_per_day = models.PositiveIntegerField(default=100)
    emails_per_month = models.PositiveIntegerField(default=1000)
    emails_per_minute = models.PositiveIntegerField(default=10)
    
    # Features enabled for this tenant
    custom_domain_allowed = models.BooleanField(default=False)
    advanced_analytics = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    bulk_email_allowed = models.BooleanField(default=False)
    
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
    
    # Status and suspension
    is_suspended = models.BooleanField(default=False)
    suspension_reason = models.TextField(blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    
    # Email reputation and health
    bounce_rate = models.FloatField(default=0.0, help_text="Bounce rate percentage")
    complaint_rate = models.FloatField(default=0.0, help_text="Complaint rate percentage")
    reputation_score = models.FloatField(default=100.0, help_text="Email reputation score (0-100)")
    
    def _ensure_counters_current(self):
        """
        Ensure daily/monthly counters are reset if date has changed.
        This prevents stale counter checks.
        """
        # Prevent recursion using thread-local guard
        guard_key = f'updating_counters_{self.tenant_id}'
        if _get_recursion_guard(guard_key):
            return
        
        today = timezone.now().date()
        needs_save = False
        
        # Reset daily counter if needed
        if self.last_daily_reset != today:
            self.emails_sent_today = 0
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
                self.save(update_fields=['emails_sent_today', 'emails_sent_this_month', 
                                        'last_daily_reset', 'last_monthly_reset'])
            finally:
                _set_recursion_guard(guard_key, False)
    
    def can_send_email(self, check_provider_limits=True, provider=None, tenant_provider=None):
        """
        Check if tenant can send email based on limits and status.
        
        Args:
            check_provider_limits: If True, also check provider-level rate limits
            provider: EmailProvider instance (for checking provider limits)
            tenant_provider: TenantEmailProvider instance (for checking tenant provider limits)
            
        Returns:
            Tuple of (can_send: bool, reason: str)
        """
        # Prevent recursion using thread-local guard
        guard_key = f'checking_send_{self.tenant_id}'
        if _get_recursion_guard(guard_key):
            # If we're already checking, return True to avoid infinite loop
            return True, "OK (recursion guard)"
        
        try:
            _set_recursion_guard(guard_key, True)
            
            # Ensure counters are current before checking limits
            self._ensure_counters_current()
            
            if not self.activated_by_root or not self.activated_by_tmd or self.is_suspended:
                return False, "Tenant email service is not activated or suspended"
                
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
            if check_provider_limits:
                from ..utils.sync_utils import RateLimitChecker
                can_send, reason = RateLimitChecker.can_send_email(
                    tenant_id=self.tenant_id,
                    provider=provider,
                    tenant_provider=tenant_provider
                )
                if not can_send:
                    return False, reason
                
            return True, "OK"
        finally:
            _set_recursion_guard(guard_key, False)
    
    def increment_usage(self):
        """Increment usage counters"""
        # Ensure counters are current (will reset if needed)
        self._ensure_counters_current()
        
        # Increment counters
        self.emails_sent_today += 1
        self.emails_sent_this_month += 1
        self.last_email_sent_at = timezone.now()
        self.save(update_fields=['emails_sent_today', 'emails_sent_this_month', 'last_email_sent_at'])

    def get_effective_from_domain(self):
        """Get the effective from domain (custom or default)"""
        if self.custom_domain_allowed and self.custom_domain and self.custom_domain_verified:
            return self.custom_domain
        return self.default_from_domain or config('DEFAULT_ORG_DOMAIN')  # fallback to organization domain (domain only)
    
    def get_effective_rate_limits(self, provider=None, tenant_provider=None):
        """
        Get effective rate limits considering global provider and tenant provider overrides.
        
        Args:
            provider: EmailProvider instance
            tenant_provider: TenantEmailProvider instance
            
        Returns:
            Dict with emails_per_minute, emails_per_hour, emails_per_day
        """
        from ..utils.sync_utils import ConfigurationHierarchy
        return ConfigurationHierarchy.get_effective_rate_limits(
            tenant_id=self.tenant_id,
            provider=provider,
            tenant_provider=tenant_provider
        )
    
    def sync_from_global_provider(self, global_provider_id=None):
        """
        Sync tenant configuration from global provider settings.
        
        Args:
            global_provider_id: Optional specific provider UUID to sync from
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        from ..utils.sync_utils import ConfigurationSync
        return ConfigurationSync.sync_tenant_from_global(
            tenant_id=str(self.tenant_id),
            global_provider_id=global_provider_id
        )
    
    def validate_configuration(self):
        """
        Validate this tenant's configuration hierarchy.
        
        Returns:
            Dict with validation results
        """
        from ..utils.sync_utils import ConfigurationValidator
        return ConfigurationValidator.validate_tenant_configuration(
            tenant_id=str(self.tenant_id)
        )

    class Meta:
        verbose_name = "Tenant Email Configuration"
        verbose_name_plural = "Tenant Email Configurations"
        indexes = [
            models.Index(fields=['tenant_id']),
            models.Index(fields=['plan_type', 'activated_by_tmd']),
        ]
    
    def __str__(self):
        return f"Email Config for Tenant {self.tenant_id} ({self.plan_type})"