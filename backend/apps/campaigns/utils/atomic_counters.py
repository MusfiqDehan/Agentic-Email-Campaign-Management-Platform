"""
Atomic usage-counter helpers.

Read-modify-write (`obj.count += 1; obj.save()`) loses updates when two
workers increment the same row concurrently. These helpers push the
increment into a single SQL UPDATE ... SET col = col + N so the database
serializes the write.
"""
from django.db.models import F
from django.utils import timezone


def increment_provider_send_counters(provider=None, organization_provider=None, count=1):
    """Atomically bump provider / org-provider send counters."""
    if count <= 0:
        return

    now = timezone.now()
    if provider is not None:
        type(provider).objects.filter(pk=provider.pk).update(
            emails_sent_today=F('emails_sent_today') + count,
            emails_sent_this_hour=F('emails_sent_this_hour') + count,
            last_used_at=now,
        )
    if organization_provider is not None:
        type(organization_provider).objects.filter(pk=organization_provider.pk).update(
            emails_sent_today=F('emails_sent_today') + count,
            emails_sent_this_hour=F('emails_sent_this_hour') + count,
            last_used_at=now,
        )


def increment_template_usage(template, count=1):
    """Atomically bump a template's usage_count."""
    if template is None or count <= 0:
        return
    type(template).objects.filter(pk=template.pk).update(
        usage_count=F('usage_count') + count
    )
