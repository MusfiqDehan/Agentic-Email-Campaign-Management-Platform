"""
Views for organization administrators to monitor team template usage.
"""
from django.db.models import Count, Q
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from core import CustomResponseMixin

from ..models import (
    TemplateUsageLog, OrganizationTemplateNotification,
    EmailTemplate
)
from ..serializers import (
    TemplateUsageLogSerializer, OrganizationTemplateNotificationSerializer
)
from ..services.template_notification_service import (
    get_unread_notifications, get_notification_count, mark_notification_as_read
)


class OrganizationTemplateUsageView(CustomResponseMixin, generics.ListAPIView):
    """
    View template usage within the organization (for org admins).
    GET /campaigns/organization/template-usage/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TemplateUsageLogSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Check if user is org admin
        if not user.organization_id:
            raise PermissionDenied("You must belong to an organization")
        
        # Check if user has admin role
        from apps.authentication.models import OrganizationMembership
        membership = OrganizationMembership.objects.filter(
            organization_id=user.organization_id,
            user=user,
            role__in=['owner', 'admin']
        ).first()
        
        if not membership and not user.is_platform_admin:
            raise PermissionDenied("Only organization admins can view team template usage")
        
        # Get usage logs for this organization
        qs = TemplateUsageLog.objects.filter(
            organization_id=user.organization_id
        ).select_related('template', 'user', 'duplicated_template')
        
        # Filters
        user_filter = self.request.query_params.get('user_id')
        category = self.request.query_params.get('category')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if user_filter:
            qs = qs.filter(user_id=user_filter)
        
        if category:
            qs = qs.filter(template__category=category)
        
        if date_from:
            qs = qs.filter(duplicated_at__gte=date_from)
        
        if date_to:
            qs = qs.filter(duplicated_at__lte=date_to)
        
        return qs.order_by('-duplicated_at')


class OrganizationTemplateNotificationsView(CustomResponseMixin, generics.ListAPIView):
    """
    Get template update notifications for the organization.
    GET /campaigns/organization/template-notifications/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrganizationTemplateNotificationSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if not user.organization_id:
            raise PermissionDenied("You must belong to an organization")
        
        qs = OrganizationTemplateNotification.objects.filter(
            organization_id=user.organization_id,
            notification__is_active=True
        ).select_related(
            'notification',
            'notification__global_template',
            'read_by'
        )
        
        # Filters
        is_read = self.request.query_params.get('is_read')
        if is_read == 'true':
            qs = qs.filter(is_read=True)
        elif is_read == 'false':
            qs = qs.filter(is_read=False)
        
        return qs.order_by('-notification__created_at')


class OrganizationTemplateNotificationMarkReadView(CustomResponseMixin, APIView):
    """
    Mark a notification as read.
    POST /campaigns/organization/template-notifications/<uuid>/mark-read/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        user = request.user
        
        if not user.organization_id:
            raise PermissionDenied("You must belong to an organization")
        
        org_notification = mark_notification_as_read(
            notification_id=pk,
            organization_id=user.organization_id,
            user=user
        )
        
        return Response({
            'message': 'Notification marked as read',
            'notification': OrganizationTemplateNotificationSerializer(org_notification).data
        })


class OrganizationTemplateUpdateStatusView(CustomResponseMixin, APIView):
    """
    Get summary of templates needing updates in the organization.
    GET /campaigns/organization/template-update-status/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if not user.organization_id:
            raise PermissionDenied("You must belong to an organization")
        
        # Get templates with source templates
        org_templates = EmailTemplate.objects.filter(
            organization_id=user.organization_id,
            is_deleted=False,
            source_template__isnull=False
        ).select_related('source_template')
        
        templates_needing_update = []
        up_to_date_templates = []
        
        for template in org_templates:
            # Get latest version of source global template
            latest_global = EmailTemplate.objects.filter(
                id=template.source_template.id,
                is_global=True,
                approval_status=EmailTemplate.ApprovalStatus.APPROVED,
                is_deleted=False
            ).first()
            
            if latest_global and latest_global.version > template.version:
                templates_needing_update.append({
                    'template_id': str(template.id),
                    'template_name': template.template_name,
                    'current_version': template.version,
                    'latest_version': latest_global.version,
                    'versions_behind': latest_global.version - template.version,
                })
            else:
                up_to_date_templates.append({
                    'template_id': str(template.id),
                    'template_name': template.template_name,
                    'version': template.version,
                })
        
        # Get notification counts
        notification_counts = get_notification_count(user.organization_id)
        
        return Response({
            'summary': {
                'total_templates': org_templates.count(),
                'needs_update': len(templates_needing_update),
                'up_to_date': len(up_to_date_templates),
                'unread_notifications': notification_counts['unread'],
            },
            'templates_needing_update': templates_needing_update,
            'up_to_date_templates': up_to_date_templates,
        })


class OrganizationTeamTemplateStatsView(CustomResponseMixin, APIView):
    """
    Get team-level statistics about template usage.
    GET /campaigns/organization/team-stats/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if not user.organization_id:
            raise PermissionDenied("You must belong to an organization")
        
        # Most used global templates by this org
        usage_by_template = TemplateUsageLog.objects.filter(
            organization_id=user.organization_id
        ).values(
            'template__id',
            'template__template_name',
            'template__category'
        ).annotate(
            usage_count=Count('id')
        ).order_by('-usage_count')[:10]
        
        # Most active team members
        usage_by_user = TemplateUsageLog.objects.filter(
            organization_id=user.organization_id
        ).values(
            'user__id',
            'user__first_name',
            'user__last_name',
            'user__email'
        ).annotate(
            templates_used=Count('id')
        ).order_by('-templates_used')[:10]
        
        # Templates by category
        templates_by_category = TemplateUsageLog.objects.filter(
            organization_id=user.organization_id
        ).values(
            'template__category'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'most_used_global_templates': list(usage_by_template),
            'most_active_team_members': list(usage_by_user),
            'templates_by_category': list(templates_by_category),
        })
