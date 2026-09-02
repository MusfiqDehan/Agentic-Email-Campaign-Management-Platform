"""
Package assignment / self-service upgrade.

All writers take a row lock on OrganizationEmailConfiguration so concurrent
upgrades cannot interleave (lost plan_type, double-assignment, or a
self-service upgrade sneaking through after an admin already moved the org).
"""
import logging

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from ..models import DomainAuditLog, OrganizationEmailConfiguration, Package
from ..models.package_models import STARTER_PACKAGE_SLUGS, STARTER_PLAN_TYPES
from . import domain_service

logger = logging.getLogger(__name__)


def is_starter_plan(package=None, plan_type=None):
    """Return True if the org is on a free/trial (self-service-upgradeable) tier."""
    if package is not None:
        return package.is_starter
    return (plan_type or 'FREE').upper() in STARTER_PLAN_TYPES


def package_rank(package):
    """Comparable rank for upgrade-vs-downgrade checks. Missing package ranks below all."""
    if package is None:
        return -1
    return package.sort_order


def get_upgrade_queryset(current_package):
    """Active packages strictly above the current tier, ordered for display."""
    qs = Package.objects.filter(is_active=True)
    if current_package is not None:
        qs = qs.exclude(pk=current_package.pk).filter(
            sort_order__gt=current_package.sort_order
        )
    else:
        qs = qs.exclude(name__in=STARTER_PACKAGE_SLUGS)
    return qs.order_by('sort_order', 'name')


def build_catalog(organization):
    """Current package + packages this org may self-service upgrade to."""
    config = domain_service.get_org_config(organization)
    current = config.package
    starter = is_starter_plan(package=current, plan_type=config.plan_type)
    upgrades = list(get_upgrade_queryset(current)) if starter else []
    return {
        'config': config,
        'current_package': current,
        'plan_type': config.plan_type,
        'is_starter': starter,
        'can_upgrade': starter and bool(upgrades),
        'available_upgrades': upgrades,
    }


def assign_package(organization, package, actor=None, *, allow_downgrade=True, require_starter=False):
    """
    Assign `package` to `organization` under a row lock.

    Args:
        allow_downgrade: platform admins may move an org to any active package.
        require_starter: self-service path — only free/trial orgs may upgrade,
            and only to a strictly higher sort_order.

    Returns:
        (config, changed: bool)  changed is False when already on `package`.
    """
    if not package.is_active:
        raise ValidationError("That package is not available.")

    with transaction.atomic():
        config = _locked_org_config(organization)
        current = config.package

        if current is not None and current.pk == package.pk:
            return config, False

        if require_starter:
            if not is_starter_plan(package=current, plan_type=config.plan_type):
                raise ValidationError(
                    "Self-service upgrades are only available on Free or Trial plans."
                )
            if package_rank(package) <= package_rank(current):
                raise ValidationError(
                    "Choose a higher-tier package than your current plan."
                )

        if not allow_downgrade and package_rank(package) < package_rank(current):
            raise ValidationError("Cannot assign a lower-tier package.")

        old_name = current.name if current else config.plan_type
        config.package = package
        config.save()

        DomainAuditLog.log(
            config, 'package_assigned', actor=actor, organization=organization,
            details={'from': old_name, 'to': package.name},
        )
        logger.info(
            "Package assigned: org=%s %s -> %s (actor=%s)",
            organization.pk, old_name, package.name,
            getattr(actor, 'pk', None),
        )
        return config, True


def upgrade_organization(organization, package_id, actor=None):
    """Self-service upgrade: starter orgs only, strictly higher package."""
    try:
        package = Package.objects.get(pk=package_id)
    except (Package.DoesNotExist, ValidationError, ValueError):
        raise ValidationError("Package not found.")
    return assign_package(
        organization, package, actor=actor,
        allow_downgrade=False, require_starter=True,
    )


def _locked_org_config(organization):
    """Load (or create) the org config and lock the row for the rest of the txn."""
    try:
        return OrganizationEmailConfiguration.objects.select_for_update().get(
            organization=organization
        )
    except OrganizationEmailConfiguration.DoesNotExist:
        try:
            OrganizationEmailConfiguration.objects.create(organization=organization)
        except IntegrityError:
            # Concurrent creator won the insert; fall through to the lock.
            pass
        return OrganizationEmailConfiguration.objects.select_for_update().get(
            organization=organization
        )
