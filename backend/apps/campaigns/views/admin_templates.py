"""
Admin views for platform administrators to manage global templates,
organizations, and approval requests.
"""
from django.db.models import Count, Q
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from apps.authentication.permissions import IsPlatformAdmin
from apps.authentication.models import Organization
from core import CustomResponseMixin

from ..models import (
    EmailTemplate, TemplateUsageLog, TemplateApprovalRequest,
    TemplateUpdateNotification
)
from ..serializers import (
    EmailTemplateSerializer, TemplateUsageLogSerializer,
    TemplateApprovalRequestSerializer
)


class AdminGlobalTemplateListCreateView(CustomResponseMixin, generics.ListCreateAPIView):
    """
    List all templates (global + org-specific) or create global templates.
    GET/POST /api/campaigns/admin/templates/
    """
    permission_classes = [IsPlatformAdmin]
    serializer_class = EmailTemplateSerializer
    
    def get_queryset(self):
        qs = EmailTemplate.objects.filter(is_deleted=False)
        
        # Filters
        is_global = self.request.query_params.get('is_global')
        organization_id = self.request.query_params.get('organization_id')
        category = self.request.query_params.get('category')
        approval_status = self.request.query_params.get('approval_status')
        include_drafts = self.request.query_params.get('include_drafts') == 'true'
        search = self.request.query_params.get('search')
        
        if is_global == 'true':
            qs = qs.filter(is_global=True)
        elif is_global == 'false':
            qs = qs.filter(is_global=False)
        
        if organization_id:
            qs = qs.filter(organization_id=organization_id)
        
        if category:
            qs = qs.filter(category=category)
        
        if approval_status:
            qs = qs.filter(approval_status=approval_status)
        
        if not include_drafts:
            qs = qs.filter(is_draft=False)
        
        if search:
            qs = qs.filter(
                Q(template_name__icontains=search) |
                Q(email_subject__icontains=search) |
                Q(description__icontains=search)
            )
        
        return qs.select_related('organization', 'source_template').order_by('-created_at')


class AdminGlobalTemplateDetailView(CustomResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete any template (admin only).
    GET/PUT/PATCH/DELETE /api/campaigns/admin/templates/<uuid>/
    """
    permission_classes = [IsPlatformAdmin]
    serializer_class = EmailTemplateSerializer
    queryset = EmailTemplate.objects.filter(is_deleted=False)
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.is_deleted = True
        instance.save()


class AdminTemplateAnalyticsView(CustomResponseMixin, APIView):
    """
    Get analytics for a specific template.
    GET /api/campaigns/admin/templates/<uuid>/analytics/
    """
    permission_classes = [IsPlatformAdmin]
    
    def get(self, request, pk):
        try:
            template = EmailTemplate.objects.get(id=pk, is_deleted=False)
        except EmailTemplate.DoesNotExist:
            raise NotFound("Template not found")
        
        # Get usage logs
        usage_logs = TemplateUsageLog.objects.filter(
            template=template
        ).select_related('organization', 'user', 'duplicated_template')
        
        # Organizations using this template
        organizations = usage_logs.values(
            'organization__id',
            'organization__name'
        ).annotate(
            usage_count=Count('id')
        ).order_by('-usage_count')
        
        # Version distribution (for global templates)
        version_distribution = []
        if template.is_global:
            # Count how many orgs are using each version
            version_counts = {}
            for log in usage_logs:
                version = log.template_version_at_duplication
                version_counts[version] = version_counts.get(version, 0) + 1
            
            version_distribution = [
                {'version': v, 'count': c}
                for v, c in sorted(version_counts.items(), reverse=True)
            ]
        
        # Recent usage
        recent_usage = TemplateUsageLogSerializer(
            usage_logs.order_by('-duplicated_at')[:10],
            many=True
        ).data
        
        return Response({
            'template': EmailTemplateSerializer(template).data,
            'analytics': {
                'total_usage': template.usage_count,
                'unique_organizations': organizations.count(),
                'organizations': list(organizations),
                'version_distribution': version_distribution,
                'recent_usage': recent_usage,
                'adoption_rate': round((organizations.count() / Organization.objects.count() * 100), 2) if Organization.objects.count() > 0 else 0
            }
        })


class AdminTemplateAnalyticsSummaryView(CustomResponseMixin, APIView):
    """
    Get overall template analytics for admin dashboard.
    GET /api/campaigns/admin/templates/analytics/summary/
    """
    permission_classes = [IsPlatformAdmin]
    
    def get(self, request):
        # Global templates stats
        global_templates = EmailTemplate.objects.filter(
            is_global=True,
            is_deleted=False,
            approval_status=EmailTemplate.ApprovalStatus.APPROVED
        )
        
        # Pending approvals
        pending_approvals = TemplateApprovalRequest.objects.filter(
            status=TemplateApprovalRequest.ApprovalStatus.PENDING
        ).count()
        
        # Total usage
        total_usage = TemplateUsageLog.objects.count()
        
        # Most used templates
        most_used = EmailTemplate.objects.filter(
            is_global=True,
            is_deleted=False
        ).order_by('-usage_count')[:5]
        
        # Recent activity
        recent_duplications = TemplateUsageLog.objects.select_related(
            'template', 'organization', 'user'
        ).order_by('-duplicated_at')[:10]
        
        # Category distribution
        category_dist = global_templates.values('category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'total_organizations': Organization.objects.count(),
            'total_global_templates': global_templates.count(),
            'total_template_usage': total_usage,
            'pending_approvals': pending_approvals,
            'summary': {
                'total_global_templates': global_templates.count(),
                'total_org_templates': EmailTemplate.objects.filter(
                    is_global=False, is_deleted=False
                ).count(),
                'pending_approvals': pending_approvals,
                'total_usage': total_usage,
            },
            'most_used_templates': EmailTemplateSerializer(most_used, many=True).data,
            'recent_duplications': TemplateUsageLogSerializer(recent_duplications, many=True).data,
            'category_distribution': list(category_dist),
        })


class AdminPendingApprovalsView(CustomResponseMixin, generics.ListAPIView):
    """
    List all pending approval requests.
    GET /api/campaigns/admin/approvals/pending/
    """
    permission_classes = [IsPlatformAdmin]
    serializer_class = TemplateApprovalRequestSerializer
    
    def get_queryset(self):
        status_filter = self.request.query_params.get('status', 'PENDING')
        
        qs = TemplateApprovalRequest.objects.select_related(
            'template', 'requested_by', 'reviewed_by'
        )
        
        if status_filter:
            qs = qs.filter(status=status_filter)
        
        return qs.order_by('-requested_at')
