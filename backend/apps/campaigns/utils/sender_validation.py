"""
Pre-send validation of from-addresses against registered sending domains.

Enforcement is scoped to domains registered in the platform:
- from-address on a SendingDomain owned by this org  -> must be one of the
  org's ACTIVE sender emails on a usable (verified, unsuspended) domain.
- from-address on a SendingDomain owned by ANOTHER org -> always rejected
  (cross-tenant spoofing).
- from-address on an unregistered domain (gmail.com, provider defaults, ...)
  -> legacy behavior, untouched. Existing tenants keep working unchanged.
"""
import logging
from email.utils import parseaddr

from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


def validate_sender(organization, from_email, raise_exception=True):
    """
    Validate `from_email` for `organization`.

    Returns the matching SenderEmail when the address is on one of the org's
    registered domains, or None when the address is outside the registered
    domain space (legacy behavior applies). Raises ValidationError on
    violation (or logs and returns None when raise_exception=False).
    """
    from ..models import SenderEmail, SendingDomain

    if not organization or not from_email:
        return None

    _, addr = parseaddr(from_email)
    addr = (addr or from_email).strip().lower()
    if '@' not in addr:
        return None
    domain_part = addr.split('@', 1)[1]

    registered = SendingDomain.objects.filter(domain=domain_part).select_related('organization').first()
    if registered is None:
        return None  # unregistered domain — legacy behavior

    problem = None
    sender = None
    if registered.organization_id != organization.id:
        problem = (
            f"The domain '{domain_part}' is registered to another organization "
            "on this platform. You cannot send from it."
        )
    else:
        sender = (
            SenderEmail.objects.filter(organization=organization, email_address__iexact=addr)
            .select_related('domain', 'domain__organization')
            .first()
        )
        if sender is None:
            problem = (
                f"'{addr}' is not a registered sender email. Create it under your "
                f"verified domain '{domain_part}' first."
            )
        elif not sender.is_usable:
            problem = (
                f"Sender email '{addr}' cannot be used right now "
                f"(address status: {sender.status}, domain status: {sender.domain.status})."
            )

    if problem:
        if raise_exception:
            raise ValidationError(problem)
        logger.warning("Sender validation failed for org %s: %s", organization.id, problem)
        return None
    return sender
