"""
Seed the DB-backed Package catalog from the legacy hardcoded PLAN_LIMITS,
assign each existing OrganizationEmailConfiguration to its matching package,
and convert legacy custom_domain values into SendingDomain rows.

Legacy domains are always created UNVERIFIED: the previous verify-domain
endpoint marked domains verified without any DNS/SES check, so prior
"verified" flags cannot be trusted.
"""
from django.db import migrations

# Snapshot of constants.PLAN_LIMITS at migration time, plus the new
# domain/sender-email limits and flags decided for each tier.
PACKAGE_SEED = {
    'free': {
        'display_name': 'Free',
        'sort_order': 0,
        'is_default': True,
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
        'max_domains': 0,
        'max_sender_emails': 0,
        'org_owned_ses_allowed': False,
    },
    'basic': {
        'display_name': 'Basic',
        'sort_order': 1,
        'is_default': False,
        'contacts_limit': 5000,
        'campaigns_per_month': 20,
        'emails_per_day': 1000,
        'emails_per_month': 10000,
        'emails_per_minute': 50,
        'batch_size': 100,
        'api_requests_per_minute': 120,
        'custom_domain_allowed': True,
        'advanced_analytics': True,
        'priority_support': False,
        'bulk_email_allowed': True,
        'ab_testing_allowed': False,
        'max_domains': 1,
        'max_sender_emails': 3,
        'org_owned_ses_allowed': False,
    },
    'professional': {
        'display_name': 'Professional',
        'sort_order': 2,
        'is_default': False,
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
        'max_domains': 3,
        'max_sender_emails': 10,
        'org_owned_ses_allowed': True,
    },
    'enterprise': {
        'display_name': 'Enterprise',
        'sort_order': 3,
        'is_default': False,
        'contacts_limit': None,
        'campaigns_per_month': None,
        'emails_per_day': 100000,
        'emails_per_month': None,
        'emails_per_minute': 1000,
        'batch_size': 1000,
        'api_requests_per_minute': 1000,
        'custom_domain_allowed': True,
        'advanced_analytics': True,
        'priority_support': True,
        'bulk_email_allowed': True,
        'ab_testing_allowed': True,
        'max_domains': None,
        'max_sender_emails': None,
        'org_owned_ses_allowed': True,
    },
}


def seed_packages(apps, schema_editor):
    Package = apps.get_model('campaigns', 'Package')
    OrganizationEmailConfiguration = apps.get_model('campaigns', 'OrganizationEmailConfiguration')
    SendingDomain = apps.get_model('campaigns', 'SendingDomain')

    packages = {}
    for name, attrs in PACKAGE_SEED.items():
        packages[name.upper()], _ = Package.objects.get_or_create(name=name, defaults=attrs)

    for config in OrganizationEmailConfiguration.objects.all().iterator():
        package = packages.get((config.plan_type or 'FREE').upper(), packages['FREE'])
        config.package = package
        config.save(update_fields=['package'])

        # Convert the legacy single custom_domain into a SendingDomain row.
        domain = (config.custom_domain or '').strip().lower().rstrip('.')
        if domain and not SendingDomain.objects.filter(domain=domain, is_deleted=False).exists():
            SendingDomain.objects.create(
                organization_id=config.organization_id,
                domain=domain,
                ownership_mode='PLATFORM',
                status='PENDING_VERIFICATION',
                legacy=True,
            )


def unseed_packages(apps, schema_editor):
    Package = apps.get_model('campaigns', 'Package')
    OrganizationEmailConfiguration = apps.get_model('campaigns', 'OrganizationEmailConfiguration')
    SendingDomain = apps.get_model('campaigns', 'SendingDomain')
    OrganizationEmailConfiguration.objects.update(package=None)
    SendingDomain.objects.filter(legacy=True).delete()
    Package.objects.filter(name__in=list(PACKAGE_SEED)).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('campaigns', '0004_package_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_packages, unseed_packages),
    ]
