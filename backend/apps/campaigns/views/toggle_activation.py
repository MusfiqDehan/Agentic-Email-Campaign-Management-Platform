from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from core.mixins import CustomResponseMixin

from automation_rule.models import (
    AutomationRule,
    EmailTemplate,
    SMSConfigurationModel,
    SMSTemplate,
    EmailProvider,
    TenantEmailConfiguration
)
from automation_rule.serializers import (
    AutomationRuleSerializer,
    EmailTemplateSerializer,
    SMSConfigurationSerializer,
    SMSTemplateSerializer,
    EmailProviderSerializer,
    TenantEmailConfigurationSerializer
)


class _BaseTMDToggleView(CustomResponseMixin, generics.GenericAPIView):
    permission_classes = [AllowAny]

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.activated_by_tmd = not instance.activated_by_tmd
        instance.save(update_fields=['activated_by_tmd', 'updated_at'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class AutomationRuleActivationForTMDToggleView(_BaseTMDToggleView):
    queryset = AutomationRule.all_objects.filter(activated_by_root=True)
    serializer_class = AutomationRuleSerializer


class EmailTemplateActivationForTMDToggleView(_BaseTMDToggleView):
    queryset = EmailTemplate.all_objects.filter(activated_by_root=True)
    serializer_class = EmailTemplateSerializer


class SMSConfigurationActivationForTMDToggleView(_BaseTMDToggleView):
    queryset = SMSConfigurationModel.all_objects.filter(activated_by_root=True)
    serializer_class = SMSConfigurationSerializer


class SMSTemplateActivationForTMDToggleView(_BaseTMDToggleView):
    queryset = SMSTemplate.all_objects.filter(activated_by_root=True)
    serializer_class = SMSTemplateSerializer


class EmailProviderActivationForTMDToggleView(_BaseTMDToggleView):
    """Toggle activation status for Email Providers by TMD"""
    queryset = EmailProvider.all_objects.filter(activated_by_root=True)
    serializer_class = EmailProviderSerializer


class TenantEmailConfigActivationForTMDToggleView(_BaseTMDToggleView):
    """Toggle activation status for Tenant Email Configuration by TMD"""
    queryset = TenantEmailConfiguration.all_objects.filter(activated_by_root=True)
    serializer_class = TenantEmailConfigurationSerializer