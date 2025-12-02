"""
Admin views for platform administrators.

These endpoints are for platform-level operations like managing shared providers.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from ..models import EmailProvider, OrganizationEmailConfiguration
from ..serializers import EmailProviderSerializer


class IsPlatformAdmin(IsAdminUser):
    """
    Permission class for platform administrators.
    
    Platform admins can manage shared providers and view all organizations.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class AdminEmailProviderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for platform admins to manage shared email providers.
    
    Endpoints:
    - GET /admin/providers/ - List all providers (shared and org-owned)
    - POST /admin/providers/ - Create a shared provider
    - GET /admin/providers/{id}/ - Get provider details
    - PUT /admin/providers/{id}/ - Update provider
    - DELETE /admin/providers/{id}/ - Delete provider
    - POST /admin/providers/{id}/set-default/ - Set as default shared provider
    - POST /admin/providers/{id}/health-check/ - Run health check
    """
    
    serializer_class = EmailProviderSerializer
    permission_classes = [IsPlatformAdmin]
    
    def get_queryset(self):
        """Return shared providers or all providers for superusers."""
        queryset = EmailProvider.objects.filter(is_deleted=False)
        
        # Filter to shared providers only unless superuser
        if not self.request.user.is_superuser:
            queryset = queryset.filter(is_shared=True)
        
        # Filter by type
        provider_type = self.request.query_params.get('type')
        if provider_type:
            queryset = queryset.filter(provider_type=provider_type)
        
        # Filter by health status
        health = self.request.query_params.get('health')
        if health:
            queryset = queryset.filter(health_status=health)
        
        return queryset.order_by('priority', 'name')
    
    def perform_create(self, serializer):
        """Create a shared provider."""
        serializer.save(
            is_shared=True,
            organization=None  # Shared providers have no organization
        )
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set provider as default shared provider."""
        provider = self.get_object()
        
        if not provider.is_shared:
            return Response(
                {'error': 'Only shared providers can be set as default'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        provider.is_default = True
        provider.save()
        
        return Response({
            'message': f'{provider.name} is now the default shared provider',
            'provider_id': str(provider.id)
        })
    
    @action(detail=True, methods=['post'])
    def health_check(self, request, pk=None):
        """Run health check on provider."""
        provider = self.get_object()
        
        # TODO: Implement actual health check logic
        from django.utils import timezone
        
        # For now, just update last check time
        provider.last_health_check = timezone.now()
        provider.health_status = 'HEALTHY'
        provider.save()
        
        return Response({
            'provider_id': str(provider.id),
            'provider_name': provider.name,
            'health_status': provider.health_status,
            'last_health_check': provider.last_health_check
        })
    
    @action(detail=True, methods=['post'])
    def test_send(self, request, pk=None):
        """Send a test email using this provider."""
        provider = self.get_object()
        
        test_email = request.data.get('email')
        if not test_email:
            return Response(
                {'error': 'email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Implement actual test send logic
        return Response({
            'message': f'Test email queued for {test_email}',
            'provider': provider.name
        })


class AdminOrganizationConfigViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for platform admins to view organization configurations.
    
    Endpoints:
    - GET /admin/organizations/ - List all organization configs
    - GET /admin/organizations/{id}/ - Get organization config details
    - POST /admin/organizations/{id}/suspend/ - Suspend organization
    - POST /admin/organizations/{id}/unsuspend/ - Unsuspend organization
    - POST /admin/organizations/{id}/upgrade-plan/ - Upgrade organization plan
    """
    
    permission_classes = [IsPlatformAdmin]
    
    def get_queryset(self):
        return OrganizationEmailConfiguration.objects.filter(
            is_deleted=False
        ).select_related('organization')
    
    def get_serializer_class(self):
        from ..serializers import TenantEmailConfigurationSerializer
        return TenantEmailConfigurationSerializer
    
    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend an organization's email service."""
        config = self.get_object()
        
        reason = request.data.get('reason', 'Suspended by platform admin')
        
        from django.utils import timezone
        config.is_suspended = True
        config.suspension_reason = reason
        config.suspended_at = timezone.now()
        config.save()
        
        return Response({
            'message': f'Organization {config.organization.name} has been suspended',
            'reason': reason
        })
    
    @action(detail=True, methods=['post'])
    def unsuspend(self, request, pk=None):
        """Unsuspend an organization's email service."""
        config = self.get_object()
        
        config.is_suspended = False
        config.suspension_reason = ''
        config.suspended_at = None
        config.save()
        
        return Response({
            'message': f'Organization {config.organization.name} has been unsuspended'
        })
    
    @action(detail=True, methods=['post'])
    def upgrade_plan(self, request, pk=None):
        """Upgrade an organization's plan."""
        config = self.get_object()
        
        new_plan = request.data.get('plan_type')
        if not new_plan:
            return Response(
                {'error': 'plan_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        valid_plans = ['FREE', 'BASIC', 'PROFESSIONAL', 'ENTERPRISE']
        if new_plan.upper() not in valid_plans:
            return Response(
                {'error': f'Invalid plan. Must be one of: {valid_plans}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_plan = config.plan_type
        config.plan_type = new_plan.upper()
        config.save()  # This will auto-sync plan limits
        
        return Response({
            'message': f'Organization {config.organization.name} upgraded from {old_plan} to {config.plan_type}',
            'new_limits': config.plan_limits
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get platform-wide statistics."""
        from django.db.models import Sum, Avg
        
        configs = self.get_queryset()
        
        stats = configs.aggregate(
            total_orgs=Count('id'),
            total_emails_today=Sum('emails_sent_today'),
            total_emails_month=Sum('emails_sent_this_month'),
            avg_bounce_rate=Avg('bounce_rate'),
            avg_complaint_rate=Avg('complaint_rate'),
        )
        
        plan_breakdown = configs.values('plan_type').annotate(
            count=Count('id')
        ).order_by('plan_type')
        
        suspended_count = configs.filter(is_suspended=True).count()
        
        return Response({
            'total_organizations': stats['total_orgs'],
            'total_emails_today': stats['total_emails_today'] or 0,
            'total_emails_this_month': stats['total_emails_month'] or 0,
            'average_bounce_rate': round(stats['avg_bounce_rate'] or 0, 2),
            'average_complaint_rate': round(stats['avg_complaint_rate'] or 0, 4),
            'suspended_organizations': suspended_count,
            'plan_breakdown': list(plan_breakdown)
        })


# Import Count for stats
from django.db.models import Count
