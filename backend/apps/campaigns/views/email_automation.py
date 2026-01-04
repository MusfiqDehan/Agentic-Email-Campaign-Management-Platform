from django.utils.dateparse import parse_datetime
from django.db.models import Q

from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from ..models import EmailTemplate, SMSTemplate, AutomationRule, EmailDeliveryLog
from ..serializers import EmailTemplateSerializer, AutomationRuleSerializer, EnhancedEmailDeliveryLogSerializer
from apps.authentication.permissions import IsPlatformAdmin
from core import CustomResponseMixin



# Utility to check if tenant can create resources
# NOTE: This function was dependent on service_integration module which is deprecated
def is_service_enabled_for_td(service_id, tenant_id):
    # Legacy implementation - service_integration module no longer exists
    # For now, return True to allow operations. Should be refactored with new architecture.
    return True

def _qp_bool(request, name):
    val = request.query_params.get(name)
    if val is None:
        return None
    val = val.lower()
    if val in ('true', '1', 'yes', 'y'):
        return True
    if val in ('false', '0', 'no', 'n'):
        return False
    return None


# EmailTemplate Views
class EmailTemplateListCreateView(CustomResponseMixin, generics.ListCreateAPIView):
    """
    List and create email templates.
    Returns global templates (approved) + user's organization templates.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = EmailTemplateSerializer

    def get_queryset(self):
        user = self.request.user
        template_type = self.request.query_params.get('template_type', 'all')
        category = self.request.query_params.get('category')
        has_updates = self.request.query_params.get('has_updates')
        
        # Base queryset - not deleted templates
        qs = EmailTemplate.objects.filter(is_deleted=False)
        
        # Build query based on template_type
        if template_type == 'global':
            # Only approved global templates
            qs = qs.filter(
                is_global=True,
                approval_status=EmailTemplate.ApprovalStatus.APPROVED,
                is_draft=False
            )
        elif template_type == 'organization':
            # Only organization's templates
            if not user.organization_id:
                return EmailTemplate.objects.none()
            qs = qs.filter(
                is_global=False,
                organization_id=user.organization_id
            )
        else:  # 'all'
            # Global (approved) + organization templates
            if user.organization_id:
                qs = qs.filter(
                    Q(is_global=True, approval_status=EmailTemplate.ApprovalStatus.APPROVED, is_draft=False) |
                    Q(is_global=False, organization_id=user.organization_id)
                )
            else:
                # User without organization can only see global templates
                qs = qs.filter(
                    is_global=True,
                    approval_status=EmailTemplate.ApprovalStatus.APPROVED,
                    is_draft=False
                )
        
        # Filter by category if provided
        if category:
            qs = qs.filter(category=category)
        
        # Filter templates with updates available
        if has_updates == 'true':
            # This requires checking source template versions
            # For now, filter templates that have a source_template
            qs = qs.filter(source_template__isnull=False)
        
        return qs.select_related('organization', 'source_template', 'duplicated_by')
    
    def create(self, request, *args, **kwargs):
        # Ensure organization_id is set for non-global templates
        if not request.data.get('is_global'):
            if 'organization_id' not in request.data:
                if request.user.organization_id:
                    request.data['organization_id'] = str(request.user.organization_id)
                else:
                    return Response(
                        {'error': 'Organization ID required for non-global templates'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        return super().create(request, *args, **kwargs)


class EmailTemplateDetailView(CustomResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an email template.
    Users can only modify their organization's templates unless they're platform admins.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = EmailTemplateSerializer

    def get_queryset(self):
        user = self.request.user
        qs = EmailTemplate.objects.filter(is_deleted=False)
        
        # Platform admins can see all templates
        if user.is_platform_admin:
            return qs
        
        # Regular users can see global templates + their org templates
        if user.organization_id:
            return qs.filter(
                Q(is_global=True, approval_status=EmailTemplate.ApprovalStatus.APPROVED) |
                Q(organization_id=user.organization_id)
            )
        else:
            # Users without org can only see global templates
            return qs.filter(
                is_global=True,
                approval_status=EmailTemplate.ApprovalStatus.APPROVED
            )
    
    def perform_update(self, serializer):
        """Validate user can edit this template."""
        template = self.get_object()
        user = self.request.user
        
        # Platform admins can edit anything
        if not user.is_platform_admin:
            # Global templates can only be edited by platform admins
            if template.is_global:
                raise PermissionDenied("Only platform admins can edit global templates")
            
            # Check organization ownership
            if not user.organization_id or str(template.organization_id) != str(user.organization_id):
                raise PermissionDenied("You can only edit templates from your organization")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Validate user can delete this template."""
        user = self.request.user
        force = self.request.query_params.get('force') == 'true'
        
        # Platform admins can delete anything
        if not user.is_platform_admin:
            # Global templates can only be deleted by platform admins
            if instance.is_global:
                raise PermissionDenied("Only platform admins can delete global templates")
            
            # Check organization ownership
            if not user.organization_id or str(instance.organization_id) != str(user.organization_id):
                raise PermissionDenied("You can only delete templates from your organization")
        
        # Prevent deleting global templates with usage unless forced
        if instance.is_global and instance.usage_count > 0:
            if not force or not user.is_platform_admin:
                raise ValidationError(
                    f"This global template has been used {instance.usage_count} times. "
                    "Cannot delete without force parameter (admin only)."
                )
        
        # Soft delete
        instance.is_deleted = True
        instance.save()


# AutomationRule Views
class AutomationRuleListCreateView(CustomResponseMixin, generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = AutomationRuleSerializer

    def get_queryset(self):
        tenant_id = self.request.query_params.get('tenant_id')
        activated_by_tmd = _qp_bool(self.request, 'activated_by_tmd')
        activated_by_td = _qp_bool(self.request, 'activated_by_td')

        qs = AutomationRule.objects.filter(activated_by_root=True)
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        if activated_by_tmd is not None:
            qs = qs.filter(activated_by_tmd=activated_by_tmd)
        if activated_by_td is not None:
            qs = qs.filter(activated_by_td=activated_by_td)
        return qs

    def create(self, request, *args, **kwargs):
        tenant_id = request.data.get('tenant_id') or request.query_params.get('tenant_id')
        service_id = request.data.get('service_id') or request.query_params.get('service_id')
        if tenant_id and service_id:
            if not is_service_enabled_for_td(service_id, tenant_id):
                raise ValidationError("Service is not enabled for tenant-specific automation rule.")
            request.data['tenant_id'] = tenant_id
        return super().create(request, *args, **kwargs)


class AutomationRuleDetailView(CustomResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = AutomationRuleSerializer

    def get_queryset(self):
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return AutomationRule.objects.filter(tenant_id=tenant_id)
        return AutomationRule.objects.filter(tenant_id__isnull=True)
    

class AutomationStatsView(CustomResponseMixin, APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        organization_id = request.query_params.get('organization_id')

        email_template_qs = EmailTemplate.objects.filter(is_deleted=False)
        sms_template_qs = SMSTemplate.objects.filter(is_deleted=False)
        rule_qs = AutomationRule.objects.filter(is_deleted=False)

        if organization_id:
            email_template_qs = email_template_qs.filter(organization_id=organization_id)
            sms_template_qs = sms_template_qs.filter(organization_id=organization_id)
            rule_qs = rule_qs.filter(organization_id=organization_id)

        data = {
            "total_templates": email_template_qs.count() + sms_template_qs.count(),
            "total_automation_rules": rule_qs.count(),
        }
        return Response(data)
    

class EmailDispatchReportView(CustomResponseMixin, generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EnhancedEmailDeliveryLogSerializer

    def get_queryset(self):
        qs = EmailDeliveryLog.objects.all()
        qp = self.request.query_params

        reason_name = qp.get('reason_name')
        status_val = qp.get('status')
        rule_id = qp.get('rule_id')
        tenant_id = qp.get('tenant_id')
        product_id = qp.get('product_id')
        scope = qp.get('scope')

        if reason_name:
            qs = qs.filter(reason_name=reason_name)
        if status_val:
            qs = qs.filter(delivery_status=status_val)
        if rule_id:
            qs = qs.filter(automation_rule__id=rule_id)
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        if product_id:
            qs = qs.filter(product_id=product_id)
        if scope:
            scope = scope.upper()
            if scope in {'GLOBAL', 'TENANT'}:
                qs = qs.filter(log_scope=scope)

        start = parse_datetime(qp.get('start')) if qp.get('start') else None
        end = parse_datetime(qp.get('end')) if qp.get('end') else None
        if start:
            qs = qs.filter(sent_at__gte=start)
        if end:
            qs = qs.filter(sent_at__lte=end)

        return qs.order_by('-sent_at')