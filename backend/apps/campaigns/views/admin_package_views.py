"""
Platform-admin API for packages, per-org limit overrides, the sending-domains
feature toggle, and cross-tenant domain / sender-email control.

Follows the admin_views.py conventions: APIView + IsPlatformAdmin +
success()/error() envelope from apps.utils.responses.
"""
import logging

from django.core.exceptions import ValidationError
from django.db.models import Count, ProtectedError
from django.shortcuts import get_object_or_404
from rest_framework import status

from rest_framework.views import APIView

from apps.authentication.models import Organization
from apps.authentication.permissions import IsPlatformAdmin
from apps.utils.responses import error, success
from ..models import (
    DomainAuditLog,
    Package,
    SenderEmail,
    SendingDomain,
)
from ..models.package_models import PACKAGE_FLAG_FIELDS, PACKAGE_LIMIT_FIELDS
from ..serializers.domain_serializers import (
    PackageSerializer,
    SenderEmailCreateSerializer,
    SenderEmailSerializer,
    SendingDomainCreateSerializer,
    SendingDomainSerializer,
)
from ..services import domain_service

logger = logging.getLogger(__name__)

OVERRIDABLE_KEYS = set(PACKAGE_LIMIT_FIELDS) | set(PACKAGE_FLAG_FIELDS)


# =============================================================================
# PACKAGES
# =============================================================================

class AdminPackageListCreateView(APIView):
    """GET/POST /admin/packages/"""

    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        packages = Package.objects.all().annotate(organization_count=Count('organizations'))
        return success(data=PackageSerializer(packages, many=True).data)

    def post(self, request):
        serializer = PackageSerializer(data=request.data)
        if not serializer.is_valid():
            return error(message="Invalid package data", errors=serializer.errors)
        package = serializer.save()
        DomainAuditLog.log(package, 'created', actor=request.user, organization=None)
        return success(
            data=PackageSerializer(package).data,
            message=f"Package '{package.name}' created",
            status_code=status.HTTP_201_CREATED,
        )


class AdminPackageDetailView(APIView):
    """GET/PATCH/DELETE /admin/packages/<uuid:pk>/"""

    permission_classes = [IsPlatformAdmin]

    def get(self, request, pk):
        package = get_object_or_404(
            Package.objects.annotate(organization_count=Count('organizations')), pk=pk
        )
        return success(data=PackageSerializer(package).data)

    def patch(self, request, pk):
        package = get_object_or_404(Package, pk=pk)
        serializer = PackageSerializer(package, data=request.data, partial=True)
        if not serializer.is_valid():
            return error(message="Invalid package data", errors=serializer.errors)
        serializer.save()
        # Changing a package changes limits for every org on it — refresh the
        # denormalized limit fields on affected configs.
        for config in package.organizations.all():
            config.sync_plan_limits()
            config.save()
        return success(data=serializer.data, message=f"Package '{package.name}' updated")

    def delete(self, request, pk):
        package = get_object_or_404(Package, pk=pk)
        try:
            package.hard_delete()
        except ProtectedError:
            count = package.organizations.count()
            return error(
                message=f"Cannot delete: {count} organization(s) are assigned to this package. "
                        "Reassign them first."
            )
        return success(message=f"Package '{package.name}' deleted")


# =============================================================================
# ORGANIZATION PACKAGE / LIMITS / FEATURE CONTROL
# =============================================================================

class AdminOrganizationAssignPackageView(APIView):
    """POST /admin/organizations/<uuid:pk>/assign-package/  body: {package_id}"""

    permission_classes = [IsPlatformAdmin]

    def post(self, request, pk):
        organization = get_object_or_404(Organization, pk=pk)
        package_id = request.data.get('package_id')
        if not package_id:
            return error(message='package_id is required')
        package = get_object_or_404(Package, pk=package_id, is_active=True)

        from ..services.package_service import assign_package
        try:
            config, changed = assign_package(
                organization, package, actor=request.user, allow_downgrade=True
            )
        except ValidationError as exc:
            return error(message='; '.join(exc.messages))

        return success(
            message=(
                f"{organization.name} is already on package '{package.name}'"
                if not changed
                else f"{organization.name} assigned to package '{package.name}'"
            ),
            data={
                'package': PackageSerializer(package).data,
                'effective_limits': config.get_effective_limits(),
                'changed': changed,
            },
        )


class AdminOrganizationLimitOverridesView(APIView):
    """
    GET/PATCH /admin/organizations/<uuid:pk>/limit-overrides/

    PATCH merges the given keys into limit_overrides; a null value clears the
    override for that key. Only known limit/flag keys are accepted.
    """

    permission_classes = [IsPlatformAdmin]

    def get(self, request, pk):
        organization = get_object_or_404(Organization, pk=pk)
        config = domain_service.get_org_config(organization)
        return success(data={
            'limit_overrides': config.limit_overrides,
            'effective_limits': config.get_effective_limits(),
            'package': config.package.name if config.package else None,
        })

    def patch(self, request, pk):
        organization = get_object_or_404(Organization, pk=pk)
        config = domain_service.get_org_config(organization)

        updates = request.data or {}
        unknown = set(updates) - OVERRIDABLE_KEYS
        if unknown:
            return error(
                message=f"Unknown limit keys: {sorted(unknown)}",
                errors={'allowed_keys': sorted(OVERRIDABLE_KEYS)},
            )

        overrides = dict(config.limit_overrides or {})
        for key, value in updates.items():
            if value is None and key in overrides:
                del overrides[key]
            elif value is not None:
                overrides[key] = value
        config.limit_overrides = overrides
        config.save()

        DomainAuditLog.log(
            config, 'limits_overridden', actor=request.user, organization=organization,
            details={'updates': {k: updates[k] for k in updates}},
        )
        return success(
            message=f"Limit overrides updated for {organization.name}",
            data={
                'limit_overrides': config.limit_overrides,
                'effective_limits': config.get_effective_limits(),
            },
        )


class AdminOrganizationDomainFeatureView(APIView):
    """POST /admin/organizations/<uuid:pk>/domain-feature/  body: {enabled: bool}"""

    permission_classes = [IsPlatformAdmin]

    def post(self, request, pk):
        organization = get_object_or_404(Organization, pk=pk)
        enabled = request.data.get('enabled')
        if not isinstance(enabled, bool):
            return error(message="'enabled' (boolean) is required")

        config = domain_service.get_org_config(organization)
        config.domain_feature_enabled = enabled
        config.save(update_fields=['domain_feature_enabled', 'updated_at'])

        DomainAuditLog.log(
            config, 'feature_toggled', actor=request.user, organization=organization,
            details={'feature': 'sending_domains', 'enabled': enabled},
        )
        state = 'enabled' if enabled else 'disabled'
        return success(message=f"Sending-domains feature {state} for {organization.name}")


class AdminOrganizationDomainUsageView(APIView):
    """GET /admin/organizations/<uuid:pk>/domain-usage/"""

    permission_classes = [IsPlatformAdmin]

    def get(self, request, pk):
        organization = get_object_or_404(Organization, pk=pk)
        config = domain_service.get_org_config(organization)
        limits = config.get_effective_limits()
        return success(data={
            'organization': organization.name,
            'package': config.package.name if config.package else config.plan_type,
            'domain_feature_enabled': config.domain_feature_enabled,
            'domains': {
                'used': SendingDomain.objects.filter(organization=organization).count(),
                'limit': limits.get('max_domains', 0),
            },
            'sender_emails': {
                'used': SenderEmail.objects.filter(organization=organization).count(),
                'limit': limits.get('max_sender_emails', 0),
            },
        })


# =============================================================================
# CROSS-TENANT DOMAIN / SENDER EMAIL CONTROL
# =============================================================================

class AdminSendingDomainListView(APIView):
    """GET /admin/domains/?organization=<uuid>&status=<status>"""

    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        domains = SendingDomain.objects.select_related('organization').all()
        organization_id = request.query_params.get('organization')
        if organization_id:
            domains = domains.filter(organization_id=organization_id)
        status_filter = request.query_params.get('status')
        if status_filter:
            domains = domains.filter(status=status_filter.upper())
        return success(data=SendingDomainSerializer(domains, many=True).data)


class AdminSendingDomainSuspendView(APIView):
    """POST /admin/domains/<uuid:pk>/suspend/  body: {reason}"""

    permission_classes = [IsPlatformAdmin]

    def post(self, request, pk):
        domain = get_object_or_404(SendingDomain, pk=pk)
        if domain.status == SendingDomain.STATUS_SUSPENDED:
            return error(message=f"Domain {domain.domain} is already suspended")
        domain_service.suspend_domain(
            domain, reason=request.data.get('reason', ''), actor=request.user
        )
        return success(
            message=f"Domain {domain.domain} suspended",
            data=SendingDomainSerializer(domain).data,
        )


class AdminSendingDomainReactivateView(APIView):
    """POST /admin/domains/<uuid:pk>/reactivate/"""

    permission_classes = [IsPlatformAdmin]

    def post(self, request, pk):
        domain = get_object_or_404(SendingDomain, pk=pk)
        if domain.status != SendingDomain.STATUS_SUSPENDED:
            return error(message=f"Domain {domain.domain} is not suspended")
        domain_service.reactivate_domain(domain, actor=request.user)
        return success(
            message=f"Domain {domain.domain} reactivated",
            data=SendingDomainSerializer(domain).data,
        )


class AdminSenderEmailSuspendView(APIView):
    """POST /admin/sender-emails/<uuid:pk>/suspend/  body: {reason}"""

    permission_classes = [IsPlatformAdmin]

    def post(self, request, pk):
        sender = get_object_or_404(SenderEmail, pk=pk)
        if sender.status == SenderEmail.STATUS_SUSPENDED:
            return error(message=f"{sender.email_address} is already suspended")
        domain_service.suspend_sender_email(
            sender, reason=request.data.get('reason', ''), actor=request.user
        )
        return success(
            message=f"Sender email {sender.email_address} suspended",
            data=SenderEmailSerializer(sender).data,
        )


class AdminSenderEmailReactivateView(APIView):
    """POST /admin/sender-emails/<uuid:pk>/reactivate/"""

    permission_classes = [IsPlatformAdmin]

    def post(self, request, pk):
        sender = get_object_or_404(SenderEmail, pk=pk)
        if sender.status != SenderEmail.STATUS_SUSPENDED:
            return error(message=f"{sender.email_address} is not suspended")
        domain_service.reactivate_sender_email(sender, actor=request.user)
        return success(
            message=f"Sender email {sender.email_address} reactivated",
            data=SenderEmailSerializer(sender).data,
        )


# =============================================================================
# ADMIN-ON-BEHALF CREATION (concierge onboarding)
# =============================================================================

class AdminOrganizationDomainCreateView(APIView):
    """POST /admin/organizations/<uuid:pk>/domains/ — create a domain on behalf
    of an org. Runs the exact same validation path as org self-service."""

    permission_classes = [IsPlatformAdmin]

    def post(self, request, pk):
        organization = get_object_or_404(Organization, pk=pk)
        serializer = SendingDomainCreateSerializer(
            data=request.data, context={'organization': organization}
        )
        if not serializer.is_valid():
            return error(message="Invalid domain data", errors=serializer.errors)
        data = serializer.validated_data
        try:
            domain = domain_service.register_domain(
                organization=organization,
                domain_name=data['domain'],
                ownership_mode=data['ownership_mode'],
                provider=data.get('provider'),
                mail_from_subdomain=data.get('mail_from_subdomain') or 'mail',
                actor=request.user,
            )
        except ValidationError as exc:
            return error(message='; '.join(exc.messages))
        return success(
            data=SendingDomainSerializer(domain).data,
            message=f"Domain {domain.domain} registered for {organization.name}",
            status_code=status.HTTP_201_CREATED,
        )


class AdminOrganizationSenderEmailCreateView(APIView):
    """POST /admin/organizations/<uuid:pk>/sender-emails/ — create a sender
    email on behalf of an org."""

    permission_classes = [IsPlatformAdmin]

    def post(self, request, pk):
        organization = get_object_or_404(Organization, pk=pk)
        serializer = SenderEmailCreateSerializer(
            data=request.data, context={'organization': organization}
        )
        if not serializer.is_valid():
            return error(message="Invalid sender email data", errors=serializer.errors)
        data = serializer.validated_data
        try:
            sender = domain_service.create_sender_email(
                organization=organization,
                domain=serializer.context['domain'],
                local_part=data['local_part'],
                display_name=data.get('display_name', ''),
                actor=request.user,
            )
        except ValidationError as exc:
            return error(message='; '.join(exc.messages))
        return success(
            data=SenderEmailSerializer(sender).data,
            message=f"Sender email {sender.email_address} created for {organization.name}",
            status_code=status.HTTP_201_CREATED,
        )
