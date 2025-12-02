"""
Constants and plan configuration for the campaigns app.
"""

# Plan tiers with their limits
PLAN_LIMITS = {
    'FREE': {
        'contacts_limit': 500,
        'campaigns_per_month': 5,
        'emails_per_day': 100,
        'emails_per_month': 1000,
        'emails_per_minute': 10,
        'batch_size': 50,
        'api_requests_per_minute': 60,
        'custom_domain_allowed': False,
        'advanced_analytics': False,
        'priority_support': False,
        'bulk_email_allowed': False,
        'ab_testing_allowed': False,
    },
    'BASIC': {
        'contacts_limit': 5000,
        'campaigns_per_month': 20,
        'emails_per_day': 1000,
        'emails_per_month': 10000,
        'emails_per_minute': 50,
        'batch_size': 100,
        'api_requests_per_minute': 120,
        'custom_domain_allowed': False,
        'advanced_analytics': True,
        'priority_support': False,
        'bulk_email_allowed': True,
        'ab_testing_allowed': False,
    },
    'PROFESSIONAL': {
        'contacts_limit': 50000,
        'campaigns_per_month': 100,
        'emails_per_day': 10000,
        'emails_per_month': 100000,
        'emails_per_minute': 200,
        'batch_size': 500,
        'api_requests_per_minute': 300,
        'custom_domain_allowed': True,
        'advanced_analytics': True,
        'priority_support': True,
        'bulk_email_allowed': True,
        'ab_testing_allowed': True,
    },
    'ENTERPRISE': {
        'contacts_limit': None,  # Unlimited
        'campaigns_per_month': None,  # Unlimited
        'emails_per_day': 100000,
        'emails_per_month': None,  # Unlimited
        'emails_per_minute': 1000,
        'batch_size': 1000,
        'api_requests_per_minute': 1000,
        'custom_domain_allowed': True,
        'advanced_analytics': True,
        'priority_support': True,
        'bulk_email_allowed': True,
        'ab_testing_allowed': True,
    },
}


def get_plan_limits(plan_type: str) -> dict:
    """
    Get limits for a specific plan type.
    
    Args:
        plan_type: One of 'FREE', 'BASIC', 'PROFESSIONAL', 'ENTERPRISE'
        
    Returns:
        Dictionary of plan limits
    """
    return PLAN_LIMITS.get(plan_type.upper(), PLAN_LIMITS['FREE'])


def get_default_plan_limits_json() -> dict:
    """
    Get the default plan limits as a JSON-serializable dict for storing in plan_limits field.
    """
    return get_plan_limits('FREE')


# Bulk operation thresholds
BULK_OPERATION_ASYNC_THRESHOLD = 1000  # Operations with more than this go to Celery

# Contact status choices
CONTACT_STATUS_CHOICES = [
    ('ACTIVE', 'Active'),
    ('UNSUBSCRIBED', 'Unsubscribed'),
    ('BOUNCED', 'Bounced'),
    ('COMPLAINED', 'Complained'),
    ('PENDING', 'Pending Verification'),
]

# Campaign status choices
CAMPAIGN_STATUS_CHOICES = [
    ('DRAFT', 'Draft'),
    ('SCHEDULED', 'Scheduled'),
    ('SENDING', 'Sending'),
    ('SENT', 'Sent'),
    ('PAUSED', 'Paused'),
    ('CANCELLED', 'Cancelled'),
    ('FAILED', 'Failed'),
]

# Common timezone choices (subset for display)
COMMON_TIMEZONE_CHOICES = [
    ('UTC', 'UTC'),
    ('America/New_York', 'Eastern Time (US & Canada)'),
    ('America/Chicago', 'Central Time (US & Canada)'),
    ('America/Denver', 'Mountain Time (US & Canada)'),
    ('America/Los_Angeles', 'Pacific Time (US & Canada)'),
    ('Europe/London', 'London'),
    ('Europe/Paris', 'Paris'),
    ('Europe/Berlin', 'Berlin'),
    ('Asia/Tokyo', 'Tokyo'),
    ('Asia/Shanghai', 'Shanghai'),
    ('Asia/Kolkata', 'Kolkata'),
    ('Asia/Dubai', 'Dubai'),
    ('Asia/Dhaka', 'Dhaka'),
    ('Australia/Sydney', 'Sydney'),
    ('Pacific/Auckland', 'Auckland'),
]
