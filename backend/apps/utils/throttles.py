from rest_framework.throttling import SimpleRateThrottle
from django.core.cache import cache


class AuthBurstRateThrottle(SimpleRateThrottle):
    scope = 'auth_burst'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f"throttle_{self.scope}_{ident}"


class AuthSustainedRateThrottle(SimpleRateThrottle):
    scope = 'auth_sustained'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return f"throttle_{self.scope}_{ident}"


class OrganizationRateThrottle(SimpleRateThrottle):
    """
    Rate throttle based on organization's plan limits.
    
    Uses Redis cache for accurate per-minute rate limiting.
    Falls back to plan_limits.api_requests_per_minute from OrganizationEmailConfiguration.
    """
    
    scope = 'organization'
    
    # Default rate (will be overridden by plan_limits)
    THROTTLE_RATES = {
        'FREE': '60/min',
        'BASIC': '120/min',
        'PROFESSIONAL': '300/min',
        'ENTERPRISE': '1000/min',
    }
    
    def get_cache_key(self, request, view):
        """
        Generate cache key based on organization.
        """
        # Get organization from request user
        organization_id = self._get_organization_id(request)
        
        if organization_id is None:
            # Fall back to IP-based throttling for unauthenticated requests
            ident = self.get_ident(request)
            return f"throttle_{self.scope}_anon_{ident}"
        
        return f"throttle_{self.scope}_org_{organization_id}"
    
    def _get_organization_id(self, request):
        """Extract organization ID from request."""
        if not request.user or not request.user.is_authenticated:
            return None
        
        # Try to get organization from user's primary organization
        if hasattr(request.user, 'organization') and request.user.organization:
            return str(request.user.organization.id)
        
        # Try to get from request header (for API keys)
        org_header = request.headers.get('X-Organization-ID')
        if org_header:
            return org_header
        
        return None
    
    def _get_rate_limit(self, request):
        """
        Get rate limit from organization's plan_limits.
        
        Returns:
            Tuple of (num_requests, duration_in_seconds)
        """
        organization_id = self._get_organization_id(request)
        
        if organization_id is None:
            # Default rate for unauthenticated requests
            return (60, 60)  # 60 requests per minute
        
        # Try to get from cached organization config
        cache_key = f"org_rate_limit_{organization_id}"
        cached_limit = cache.get(cache_key)
        
        if cached_limit:
            return cached_limit
        
        # Fetch from database
        try:
            from campaigns.models import OrganizationEmailConfiguration
            
            config = OrganizationEmailConfiguration.objects.filter(
                organization_id=organization_id
            ).first()
            
            if config and config.plan_limits:
                rate = config.plan_limits.get('api_requests_per_minute', 60)
            else:
                # Default to FREE plan
                rate = 60
            
            result = (rate, 60)  # (requests, seconds)
            
            # Cache for 5 minutes
            cache.set(cache_key, result, 300)
            
            return result
            
        except Exception:
            # Fallback on any error
            return (60, 60)
    
    def get_rate(self):
        """
        Override to return a default rate string.
        This prevents the 'No default throttle rate set' error.
        The actual rate is determined dynamically in allow_request().
        """
        return '500/min'  # Default fallback, actual rate is dynamic
    
    def allow_request(self, request, view):
        """
        Check if request should be allowed based on organization rate limit.
        """
        self.rate = self._get_rate_limit(request)
        self.num_requests, self.duration = self.rate
        
        return super().allow_request(request, view)
    
    def parse_rate(self, rate):
        """
        Override to handle tuple rate format.
        """
        if isinstance(rate, tuple):
            return rate
        return super().parse_rate(rate)
    
    def throttle_failure(self):
        """
        Called when a request is throttled.
        """
        return False
    
    def wait(self):
        """
        Returns the recommended wait time in seconds.
        """
        if self.history:
            remaining_duration = self.duration - (self.now - self.history[-1])
            return remaining_duration
        return None


class EmailSendingRateThrottle(SimpleRateThrottle):
    """
    Rate throttle specifically for email sending operations.
    
    Uses organization's emails_per_minute limit.
    """
    
    scope = 'email_sending'
    
    def get_cache_key(self, request, view):
        """Generate cache key for email sending rate limit."""
        organization_id = self._get_organization_id(request)
        
        if organization_id is None:
            return None  # Don't throttle if no organization
        
        return f"throttle_{self.scope}_org_{organization_id}"
    
    def _get_organization_id(self, request):
        """Extract organization ID from request."""
        if not request.user or not request.user.is_authenticated:
            return None
        
        if hasattr(request.user, 'organization') and request.user.organization:
            return str(request.user.organization.id)
        
        return None
    
    def _get_email_rate_limit(self, request):
        """Get email sending rate limit from organization config."""
        organization_id = self._get_organization_id(request)
        
        if organization_id is None:
            return (10, 60)  # 10 emails per minute default
        
        cache_key = f"org_email_rate_{organization_id}"
        cached_limit = cache.get(cache_key)
        
        if cached_limit:
            return cached_limit
        
        try:
            from campaigns.models import OrganizationEmailConfiguration
            
            config = OrganizationEmailConfiguration.objects.filter(
                organization_id=organization_id
            ).first()
            
            if config:
                rate = config.emails_per_minute
            else:
                rate = 10
            
            result = (rate, 60)
            cache.set(cache_key, result, 300)
            
            return result
            
        except Exception:
            return (10, 60)
    
    def get_rate(self):
        """
        Override to return a default rate string.
        This prevents the 'No default throttle rate set' error.
        The actual rate is determined dynamically in allow_request().
        """
        return '60/min'  # Default fallback, actual rate is dynamic
    
    def allow_request(self, request, view):
        """Check if email sending request should be allowed."""
        self.rate = self._get_email_rate_limit(request)
        self.num_requests, self.duration = self.rate
        
        return super().allow_request(request, view)
    
    def parse_rate(self, rate):
        """Override to handle tuple rate format."""
        if isinstance(rate, tuple):
            return rate
        return super().parse_rate(rate)