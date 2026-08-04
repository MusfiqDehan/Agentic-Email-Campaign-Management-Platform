"""
DB-backed subscription packages (replaces the hardcoded PLAN_LIMITS catalog).

Platform admins create/edit packages and assign one to each organization via
OrganizationEmailConfiguration.package. Per-organization exceptions live in
OrganizationEmailConfiguration.limit_overrides (sparse dict, override wins).
"""
import uuid
from django.db import models
from apps.utils.base_models import BaseModel

# Keys a package contributes to the effective-limits dict. Kept aligned with
# the legacy constants.PLAN_LIMITS key shape so existing gates keep working.
PACKAGE_LIMIT_FIELDS = [
    'contacts_limit',
    'campaigns_per_month',
    'emails_per_day',
    'emails_per_month',
    'emails_per_minute',
    'batch_size',
    'api_requests_per_minute',
    'max_domains',
    'max_sender_emails',
]

PACKAGE_FLAG_FIELDS = [
    'custom_domain_allowed',
    'advanced_analytics',
    'priority_support',
    'bulk_email_allowed',
    'ab_testing_allowed',
    'org_owned_ses_allowed',
]


class Package(BaseModel):
    """
    A platform-admin-managed subscription tier.

    Integer limits use NULL to mean "unlimited". Feature flags are plain
    booleans. `get_limits_dict()` returns the same key shape as the legacy
    PLAN_LIMITS entries plus the new domain/sender-email keys.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.SlugField(max_length=50, unique=True, help_text="Stable slug, e.g. 'free', 'basic'")
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(
        default=False,
        help_text="Assigned to new organizations. Only one package can be default."
    )
    sort_order = models.PositiveIntegerField(default=0)

    # Limits (NULL = unlimited)
    contacts_limit = models.PositiveIntegerField(null=True, blank=True)
    campaigns_per_month = models.PositiveIntegerField(null=True, blank=True)
    emails_per_day = models.PositiveIntegerField(null=True, blank=True)
    emails_per_month = models.PositiveIntegerField(null=True, blank=True)
    emails_per_minute = models.PositiveIntegerField(null=True, blank=True)
    batch_size = models.PositiveIntegerField(null=True, blank=True, default=100)
    api_requests_per_minute = models.PositiveIntegerField(null=True, blank=True, default=60)
    max_domains = models.PositiveIntegerField(
        null=True, blank=True, default=0,
        help_text="Max sending domains an organization may register (NULL = unlimited)"
    )
    max_sender_emails = models.PositiveIntegerField(
        null=True, blank=True, default=0,
        help_text="Max sender email addresses across all domains (NULL = unlimited)"
    )

    # Feature flags
    custom_domain_allowed = models.BooleanField(default=False)
    advanced_analytics = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    bulk_email_allowed = models.BooleanField(default=False)
    ab_testing_allowed = models.BooleanField(default=False)
    org_owned_ses_allowed = models.BooleanField(
        default=False,
        help_text="Allow domains provisioned in the organization's own AWS SES account"
    )

    class Meta:
        verbose_name = "Package"
        verbose_name_plural = "Packages"
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.display_name or self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Enforce a single default package
        if self.is_default:
            Package.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)

    def get_limits_dict(self):
        """Return limits + flags in the legacy PLAN_LIMITS key shape."""
        limits = {field: getattr(self, field) for field in PACKAGE_LIMIT_FIELDS}
        limits.update({field: getattr(self, field) for field in PACKAGE_FLAG_FIELDS})
        return limits
