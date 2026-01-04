from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.authentication.models import OrganizationMembership, Organization


class IsEmailVerified(BasePermission):
    """Check if user is authenticated and active."""
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active)


class IsOrganizationOwnerOrAdmin(BasePermission):
    """Object-level permission for organization owners/admins."""
    
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Organization):
            # Owner can do anything
            if obj.owner_id == request.user.id:
                return True
            # Admin membership check
            return OrganizationMembership.objects.filter(
                user=request.user, 
                organization=obj, 
                role__in=['owner', 'admin']
            ).exists()
        return False


class IsOrganizationAdmin(BasePermission):
    """
    Permission class for organization admins.
    
    Checks if the authenticated user has 'owner' or 'admin' role 
    in their current organization. Use this for endpoints that 
    require organization-level admin access.
    
    Usage:
        permission_classes = [IsAuthenticated, IsOrganizationAdmin]
    """
    message = "You must be an organization owner or admin to perform this action."
    
    def has_permission(self, request, view):
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Must belong to an organization
        if not request.user.organization:
            self.message = "You must belong to an organization to perform this action."
            return False
        
        # Check if user is org owner
        if request.user.organization.owner_id == request.user.id:
            return True
        
        # Check if user has admin membership
        return OrganizationMembership.objects.filter(
            user=request.user,
            organization=request.user.organization,
            role__in=['owner', 'admin'],
            is_active=True
        ).exists()
    
    def has_object_permission(self, request, view, obj):
        """
        Object-level permission to ensure the object belongs to the user's organization.
        
        Supports objects with 'organization' or 'organization_id' attribute.
        """
        if not self.has_permission(request, view):
            return False
        
        # Get object's organization
        obj_org_id = None
        if hasattr(obj, 'organization_id'):
            obj_org_id = obj.organization_id
        elif hasattr(obj, 'organization') and obj.organization:
            obj_org_id = obj.organization.id
        
        if obj_org_id is None:
            return False
        
        # Ensure object belongs to user's organization
        return str(obj_org_id) == str(request.user.organization.id)


class ReadOnly(BasePermission):
    """Only allow read-only methods (GET, HEAD, OPTIONS)."""
    
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class IsPlatformAdmin(BasePermission):
    """
    Permission class for platform administrators.
    
    Checks if the authenticated user has platform admin privileges.
    Use this for endpoints that require system-wide administrative access.
    
    Usage:
        permission_classes = [IsPlatformAdmin]
    """
    message = "You must be a platform administrator to perform this action."
    
    def has_permission(self, request, view):
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Must be platform admin
        return getattr(request.user, 'is_platform_admin', False)