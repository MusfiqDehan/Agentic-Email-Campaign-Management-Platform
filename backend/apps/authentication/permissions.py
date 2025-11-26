from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.authentication.models import OrganizationMembership, Organization

class IsEmailVerified(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active)

class IsOrganizationOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Organization):
            # Owner can do anything
            if obj.owner_id == request.user.id:
                return True
            # Admin membership check
            return OrganizationMembership.objects.filter(user=request.user, organization=obj, role__in=['owner','admin']).exists()
        return False

class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS