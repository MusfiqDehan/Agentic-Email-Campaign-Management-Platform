from django.utils.dateparse import parse_datetime

from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import EmailTemplate, SMSTemplate, AutomationRule, EmailDeliveryLog
from ..serializers import EmailTemplateSerializer, AutomationRuleSerializer, EnhancedEmailDeliveryLogSerializer
from service_integration.models import ServiceDefinition
from core import CustomResponseMixin



# Utility to check if tenant can create resources
def is_service_enabled_for_td(service_id, tenant_id):
    try:
        service = ServiceDefinition.objects.get(id=service_id, tenant_id=tenant_id)
        return service.enabled_for_td
    except ServiceDefinition.DoesNotExist:
        # Fallback to global service definition
        try:
            service = ServiceDefinition.objects.get(id=service_id, tenant_id__isnull=True)
            return service.enabled_for_td
        except ServiceDefinition.DoesNotExist:
            return False

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
    permission_classes = [permissions.AllowAny]
    serializer_class = EmailTemplateSerializer

    def get_queryset(self):
        tenant_id = self.request.query_params.get('tenant_id')
        activated_by_tmd = _qp_bool(self.request, 'activated_by_tmd')
        activated_by_td = _qp_bool(self.request, 'activated_by_td')

        qs = EmailTemplate.objects.filter(activated_by_root=True)
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
                raise ValidationError("Service is not enabled for tenant-specific template.")
            request.data['tenant_id'] = tenant_id
        return super().create(request, *args, **kwargs)


class EmailTemplateDetailView(CustomResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EmailTemplateSerializer

    def get_queryset(self):
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return EmailTemplate.objects.filter(tenant_id=tenant_id)
        return EmailTemplate.objects.filter(tenant_id__isnull=True)


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
        tenant_id = request.query_params.get('tenant_id')
        activated_by_tmd = _qp_bool(request, 'activated_by_tmd')

        email_template_qs = EmailTemplate.objects.filter(activated_by_root=True)
        sms_template_qs = SMSTemplate.objects.filter(activated_by_root=True)
        rule_qs = AutomationRule.objects.filter(activated_by_root=True)

        if tenant_id:
            email_template_qs = email_template_qs.filter(tenant_id=tenant_id)
            sms_template_qs = sms_template_qs.filter(tenant_id=tenant_id)
            rule_qs = rule_qs.filter(tenant_id=tenant_id)
        if activated_by_tmd is not None:
            email_template_qs = email_template_qs.filter(activated_by_tmd=activated_by_tmd)
            sms_template_qs = sms_template_qs.filter(activated_by_tmd=activated_by_tmd)
            rule_qs = rule_qs.filter(activated_by_tmd=activated_by_tmd)

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