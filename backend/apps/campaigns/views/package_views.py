"""
Organization-facing package catalog and self-service upgrade.

Platform-admin CRUD lives in admin_package_views.py. These endpoints are
what the dashboard sidebar "Upgrade to Pro" dialog uses.
"""
import uuid as uuid_lib

from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.authentication.permissions import IsOrganizationAdmin
from apps.utils.responses import error, success

from ..serializers.domain_serializers import PackageSerializer
from ..services.package_service import build_catalog, upgrade_organization


class PackageCatalogView(APIView):
    """
    GET /packages/catalog/

    Current package plus the higher-tier packages this org may upgrade to.
    The upgrade CTA should only render when `can_upgrade` is true (free/trial).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization = getattr(request.user, 'organization', None)
        if not organization:
            return error(message='You must belong to an organization', status_code=403)

        catalog = build_catalog(organization)
        current = catalog['current_package']
        return success(data={
            'current_package': PackageSerializer(current).data if current else None,
            'plan_type': catalog['plan_type'],
            'is_starter': catalog['is_starter'],
            'can_upgrade': catalog['can_upgrade'],
            'available_upgrades': PackageSerializer(
                catalog['available_upgrades'], many=True
            ).data,
        })


class PackageUpgradeView(APIView):
    """
    POST /packages/upgrade/  body: {package_id}

    Free/trial organizations may move to a strictly higher-tier package.
    Concurrent clicks are serialized on the org-config row lock.
    """
    permission_classes = [IsAuthenticated, IsOrganizationAdmin]

    def post(self, request):
        organization = getattr(request.user, 'organization', None)
        if not organization:
            return error(message='You must belong to an organization', status_code=403)

        package_id = request.data.get('package_id')
        if not package_id:
            return error(message='package_id is required')
        try:
            uuid_lib.UUID(str(package_id))
        except (ValueError, TypeError, AttributeError):
            return error(message='package_id must be a valid UUID')

        try:
            config, changed = upgrade_organization(
                organization, package_id, actor=request.user
            )
        except ValidationError as exc:
            return error(message='; '.join(exc.messages))

        catalog = build_catalog(organization)
        current = catalog['current_package']
        return success(
            message=(
                f"Already on '{current.display_name}'" if not changed
                else f"Upgraded to '{current.display_name}'"
            ),
            data={
                'changed': changed,
                'current_package': PackageSerializer(current).data if current else None,
                'plan_type': catalog['plan_type'],
                'is_starter': catalog['is_starter'],
                'can_upgrade': catalog['can_upgrade'],
                'available_upgrades': PackageSerializer(
                    catalog['available_upgrades'], many=True
                ).data,
                'effective_limits': config.get_effective_limits(),
            },
        )
