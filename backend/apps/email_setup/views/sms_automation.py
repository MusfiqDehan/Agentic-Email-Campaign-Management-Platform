from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError
from ..models.sms_config_models import SMSConfigurationModel, SMSTemplate
from automation_rule.serializers import SMSConfigurationSerializer, SMSTemplateSerializer
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


class SMSConfigurationListCreateView(CustomResponseMixin, generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SMSConfigurationSerializer

    def get_queryset(self):
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return SMSConfigurationModel.objects.filter(tenant_id=tenant_id)
        return SMSConfigurationModel.objects.filter(tenant_id__isnull=True)

    def create(self, request, *args, **kwargs):
        tenant_id = request.data.get('tenant_id') or request.query_params.get('tenant_id')
        service_id = request.data.get('service_id') or request.query_params.get('service_id')
        if tenant_id and service_id:
            if not is_service_enabled_for_td(service_id, tenant_id):
                raise ValidationError("Service is not enabled for tenant-specific configuration.")
            request.data['tenant_id'] = tenant_id
        return super().create(request, *args, **kwargs)


class SMSConfigurationDetailView(CustomResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SMSConfigurationSerializer

    def get_queryset(self):
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return SMSConfigurationModel.objects.filter(tenant_id=tenant_id)
        return SMSConfigurationModel.objects.filter(tenant_id__isnull=True)


class SMSTemplateListCreateView(CustomResponseMixin, generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SMSTemplateSerializer

    def get_queryset(self):
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return SMSTemplate.objects.filter(tenant_id=tenant_id)
        return SMSTemplate.objects.filter(tenant_id__isnull=True)

    def create(self, request, *args, **kwargs):
        tenant_id = request.data.get('tenant_id') or request.query_params.get('tenant_id')
        service_id = request.data.get('service_id') or request.query_params.get('service_id')
        if tenant_id and service_id:
            if not is_service_enabled_for_td(service_id, tenant_id):
                raise ValidationError("Service is not enabled for tenant-specific template.")
            request.data['tenant_id'] = tenant_id
        return super().create(request, *args, **kwargs)


class SMSTemplateDetailView(CustomResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SMSTemplateSerializer

    def get_queryset(self):
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            return SMSTemplate.objects.filter(tenant_id=tenant_id)
        return SMSTemplate.objects.filter(tenant_id__isnull=True)


