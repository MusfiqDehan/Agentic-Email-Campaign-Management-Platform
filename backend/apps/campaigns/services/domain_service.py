"""
Domain / sender-email lifecycle operations shared by the org-facing API,
the platform-admin (on-behalf) API and the Celery verification tasks.

All limit and feature gating for the sending-domains feature lives here so
self-service and admin-on-behalf go through identical validation.
"""
import json
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from ..models import (
    DomainAuditLog,
    EmailAccount,
    Notification,
    OrganizationEmailConfiguration,
    Package,
    SenderEmail,
    SendingDomain,
)
from ..utils.ses_identity_service import SESIdentityError, SESIdentityService

logger = logging.getLogger(__name__)


def get_org_config(organization):
    """Get (or lazily create) the org's email configuration.

    get_or_create races when two requests insert the OneToOne at once;
    IntegrityError falls through to the winner's row. New configs are
    pinned to the default package so the upgrade catalog has a current tier.
    """
    try:
        config, created = OrganizationEmailConfiguration.objects.get_or_create(
            organization=organization
        )
    except IntegrityError:
        return OrganizationEmailConfiguration.objects.get(organization=organization)

    if created and not config.package_id:
        default = Package.objects.filter(is_default=True, is_active=True).first()
        if default:
            config.package = default
            config.save()
    return config


def _check_feature_enabled(config):
    if not config.domain_feature_enabled:
        raise ValidationError("The sending-domains feature is disabled for your organization.")
    if not config.is_custom_domain_allowed:
        raise ValidationError("Your current package does not include custom sending domains.")


def _notify(organization, title, message, related_object=None, metadata=None):
    """Create a Notification and broadcast it over the org's WebSocket group."""
    try:
        notification = Notification.objects.create(
            organization=organization,
            notification_type='SYSTEM_UPDATE',
            title=title,
            message=message,
            related_object_type=related_object.__class__.__name__.lower() if related_object else '',
            related_object_id=related_object.pk if related_object else None,
            metadata=metadata or {},
        )
        channel_layer = get_channel_layer()
        group_name = f"notifications_{organization.id}"
        from ..serializers import NotificationSerializer
        data = json.loads(json.dumps(NotificationSerializer(notification).data, default=str))
        async_to_sync(channel_layer.group_send)(
            group_name, {'type': 'notification_message', 'data': data}
        )
        unread = Notification.objects.filter(
            organization=organization, is_read=False, is_deleted=False
        ).count()
        async_to_sync(channel_layer.group_send)(
            group_name, {'type': 'unread_count_update', 'count': unread}
        )
    except Exception:
        logger.exception("Failed to create/broadcast domain notification")


# ---------------------------------------------------------------------------
# Domains
# ---------------------------------------------------------------------------

def register_domain(organization, domain_name, ownership_mode=SendingDomain.OWNERSHIP_PLATFORM,
                    provider=None, mail_from_subdomain='mail', actor=None):
    """
    Validate limits/uniqueness, provision the SES identity and persist the
    SendingDomain in PENDING_VERIFICATION with its DNS records.
    """
    config = get_org_config(organization)
    _check_feature_enabled(config)

    if ownership_mode == SendingDomain.OWNERSHIP_ORG and not config.is_org_owned_ses_allowed:
        raise ValidationError("Your current package does not allow org-owned SES domains.")

    max_domains = config.max_domains
    current = SendingDomain.objects.filter(organization=organization).count()
    if max_domains is not None and current >= max_domains:
        raise ValidationError(
            f"Domain limit reached ({current}/{max_domains}). "
            "Contact support to increase your package limits."
        )

    normalized = (domain_name or '').strip().lower().rstrip('.')
    if SendingDomain.all_objects.filter(domain=normalized, is_deleted=False).exists():
        raise ValidationError("This domain is already registered.")

    domain = SendingDomain(
        organization=organization,
        domain=normalized,
        ownership_mode=ownership_mode,
        provider=provider,
        mail_from_subdomain=mail_from_subdomain or 'mail',
        status=SendingDomain.STATUS_PENDING_DNS,
    )
    domain.clean()

    service = SESIdentityService(domain)
    try:
        service.create_identity()
        domain.status = SendingDomain.STATUS_PENDING_VERIFICATION
        domain.verification_error = ''
    except SESIdentityError as exc:
        # Persist anyway so the org can retry via the verify endpoint;
        # non-retryable credential problems surface to the caller.
        if not exc.retryable:
            raise ValidationError(f"Could not provision the domain in AWS SES: {exc}")
        domain.verification_error = str(exc)

    domain.save()
    DomainAuditLog.log(domain, 'created', actor=actor, details={
        'ownership_mode': ownership_mode,
        'provider_id': str(provider.pk) if provider else None,
    })
    return domain


def check_domain_verification(domain, actor=None):
    """
    Poll SES for the domain's verification status and apply transitions.
    Returns (verified: bool, detail: dict).
    """
    service = SESIdentityService(domain)
    now = timezone.now()

    try:
        # (Re-)provision first if we never got DKIM tokens (e.g. failed create).
        if not domain.dkim_tokens:
            service.create_identity()
        verified, detail = service.get_verification_status()
    except SESIdentityError as exc:
        domain.last_checked_at = now
        domain.verification_error = str(exc)
        domain.save(update_fields=['last_checked_at', 'verification_error', 'updated_at'])
        raise

    domain.last_checked_at = now
    domain.mail_from_status = detail.get('mail_from_status', '')
    domain.verification_error = ''

    newly_verified = verified and domain.status != SendingDomain.STATUS_VERIFIED
    if verified:
        domain.status = SendingDomain.STATUS_VERIFIED
        if not domain.verified_at:
            domain.verified_at = now
    elif domain.status == SendingDomain.STATUS_PENDING_DNS and detail.get('dkim_status'):
        domain.status = SendingDomain.STATUS_PENDING_VERIFICATION

    # Time out domains stuck pending for over 7 days
    if (not verified and domain.status in SendingDomain.PENDING_STATUSES
            and (now - domain.created_at).days >= 7):
        domain.status = SendingDomain.STATUS_FAILED
        domain.verification_error = (
            "DNS records were not detected within 7 days. Add the records and press "
            "'Check verification' to retry."
        )

    domain.save()

    if newly_verified:
        DomainAuditLog.log(domain, 'verified', actor=actor, details=detail)
        _notify(
            domain.organization,
            title="Domain verified",
            message=f"Your sending domain {domain.domain} is verified and ready to use.",
            related_object=domain,
            metadata={'domain': domain.domain},
        )
    elif domain.status == SendingDomain.STATUS_FAILED:
        DomainAuditLog.log(domain, 'verification_failed', actor=actor, details=detail)

    return verified, detail


def retry_domain_verification(domain, actor=None):
    """Reset a FAILED domain to pending and re-check immediately."""
    if domain.status == SendingDomain.STATUS_FAILED:
        domain.status = SendingDomain.STATUS_PENDING_VERIFICATION
        domain.save(update_fields=['status', 'updated_at'])
    return check_domain_verification(domain, actor=actor)


def delete_domain(domain, actor=None):
    """Soft-delete a domain, its sender emails and linked mailbox accounts."""
    try:
        SESIdentityService(domain).delete_identity()
    except SESIdentityError as exc:
        # Best-effort: the identity can be cleaned up manually in AWS later.
        logger.warning("Could not delete SES identity for %s: %s", domain.domain, exc)

    for sender in SenderEmail.objects.filter(domain=domain):
        delete_sender_email(sender, actor=actor, _log=False)

    domain.delete()  # BaseModel soft delete
    DomainAuditLog.log(domain, 'deleted', actor=actor)
    return domain


def suspend_domain(domain, reason='', actor=None):
    domain.previous_status = domain.status
    domain.status = SendingDomain.STATUS_SUSPENDED
    domain.suspension_reason = reason or 'Suspended by platform admin'
    domain.save(update_fields=['previous_status', 'status', 'suspension_reason', 'updated_at'])
    DomainAuditLog.log(domain, 'suspended', actor=actor, details={'reason': reason})
    _notify(
        domain.organization,
        title="Domain suspended",
        message=f"Your sending domain {domain.domain} was suspended by the platform. {reason}".strip(),
        related_object=domain,
    )
    return domain


def reactivate_domain(domain, actor=None):
    domain.status = domain.previous_status or SendingDomain.STATUS_PENDING_VERIFICATION
    domain.previous_status = ''
    domain.suspension_reason = ''
    domain.save(update_fields=['previous_status', 'status', 'suspension_reason', 'updated_at'])
    DomainAuditLog.log(domain, 'reactivated', actor=actor)
    return domain


# ---------------------------------------------------------------------------
# Sender emails
# ---------------------------------------------------------------------------

def create_sender_email(organization, domain, local_part, display_name='', actor=None):
    """Create a sender address under a verified domain, plus its inbox account
    for platform-managed domains."""
    config = get_org_config(organization)
    _check_feature_enabled(config)

    if domain.organization_id != organization.id:
        raise ValidationError("This domain does not belong to your organization.")
    if not domain.is_usable:
        raise ValidationError(
            "The domain must be verified (and not suspended) before creating sender emails."
        )

    max_senders = config.max_sender_emails
    current = SenderEmail.objects.filter(organization=organization).count()
    if max_senders is not None and current >= max_senders:
        raise ValidationError(
            f"Sender email limit reached ({current}/{max_senders}). "
            "Contact support to increase your package limits."
        )

    sender = SenderEmail(
        organization=organization,
        domain=domain,
        local_part=(local_part or '').strip().lower(),
        display_name=display_name or '',
    )
    sender.clean()
    email_address = f"{sender.local_part}@{domain.domain}"
    if SenderEmail.all_objects.filter(email_address=email_address, is_deleted=False).exists():
        raise ValidationError("This sender email address already exists.")

    sender.save()

    # Receiving is supported for platform-managed domains only in v1:
    # inbound arrives via the platform SES account (SNS/S3 -> SESInboundHandler).
    if domain.ownership_mode == SendingDomain.OWNERSHIP_PLATFORM:
        account, created = EmailAccount.all_objects.get_or_create(
            organization=organization,
            email_address=email_address,
            defaults={
                'name': display_name or sender.local_part,
                'account_type': 'AWS_SES',
                'display_name': display_name or sender.local_part,
                # Inbound arrives via the platform SES account webhook —
                # no per-account credentials or IMAP sync needed.
                'encrypted_config': '',
                'sync_enabled': False,
                'is_active': True,
            },
        )
        if not created:
            # Re-using the mailbox of a previously deleted address keeps its
            # message history; reactivate it so inbound routing resumes.
            account.is_active = True
            account.is_deleted = False
            account.deleted_at = None
            account.save(update_fields=['is_active', 'is_deleted', 'deleted_at', 'updated_at'])
        sender.mailbox_account = account
        sender.save(update_fields=['mailbox_account', 'updated_at'])

    DomainAuditLog.log(sender, 'created', actor=actor, details={'domain': domain.domain})
    return sender


def delete_sender_email(sender, actor=None, _log=True):
    """Soft-delete the address; keep mailbox history but deactivate the account."""
    if sender.mailbox_account_id:
        EmailAccount.all_objects.filter(pk=sender.mailbox_account_id).update(is_active=False)
        # Release the OneToOne link so the address can be re-created later
        # (the soft-deleted row would otherwise hold the account hostage).
        sender.mailbox_account = None
        sender.save(update_fields=['mailbox_account', 'updated_at'])
    sender.delete()  # BaseModel soft delete
    if _log:
        DomainAuditLog.log(sender, 'deleted', actor=actor)
    return sender


def suspend_sender_email(sender, reason='', actor=None):
    sender.status = SenderEmail.STATUS_SUSPENDED
    sender.suspension_reason = reason or 'Suspended by platform admin'
    sender.save(update_fields=['status', 'suspension_reason', 'updated_at'])
    DomainAuditLog.log(sender, 'suspended', actor=actor, details={'reason': reason})
    return sender


def reactivate_sender_email(sender, actor=None):
    sender.status = SenderEmail.STATUS_ACTIVE
    sender.suspension_reason = ''
    sender.save(update_fields=['status', 'suspension_reason', 'updated_at'])
    DomainAuditLog.log(sender, 'reactivated', actor=actor)
    return sender
