"""
Activation/Deactivation Toggle Views for Email Automation Resources

This module provides unified activation toggle views for:
- Global Email Providers
- Tenant Email Providers
- Tenant-Owned Email Providers
- Tenant Email Configurations
- Global Email Templates
- Tenant Email Templates
- Global Automation Rules
- Tenant Automation Rules
"""

from rest_framework import generics, permissions
from rest_framework import status
from core.mixins import CustomResponseMixin

from automation_rule.models import (
    AutomationRule, EmailTemplate, SMSConfigurationModel, SMSTemplate,
    EmailProvider, TenantEmailProvider, TenantEmailConfiguration
)
from automation_rule.serializers import (
    AutomationRuleSerializer,
    EmailTemplateSerializer,
    SMSConfigurationSerializer,
    SMSTemplateSerializer,
    EmailProviderSerializer,
    TenantEmailProviderSerializer,
    TenantEmailConfigurationSerializer,
    GlobalAutomationRuleSerializer,
    GlobalEmailTemplateSerializer
)

try:
    from automation_rule.serializers.enhanced_serializers import TenantOwnEmailProviderSerializer
except ImportError:
    TenantOwnEmailProviderSerializer = None


class _BaseActivationToggleView(CustomResponseMixin, generics.GenericAPIView):
    """
    Base view for toggling activation status of resources.
    Subclasses must define:
    - queryset
    - serializer_class
    - activation_field (name of the field to toggle, default: 'activated_by_tmd')
    """
    permission_classes = [permissions.AllowAny]
    activation_field = 'activated_by_tmd'

    def get_activation_field(self):
        """Get the name of the activation field"""
        return getattr(self, 'activation_field', 'activated_by_tmd')
    
    def patch(self, request, *args, **kwargs):
        """Toggle the activation status"""
        instance = self.get_object()
        field_name = self.get_activation_field()
        
        # Get current value and toggle it
        current_value = getattr(instance, field_name)
        new_value = not current_value
        
        # Update the field
        setattr(instance, field_name, new_value)
        instance.save(update_fields=[field_name, 'updated_at'])
        
        # Serialize the updated instance
        serializer = self.get_serializer(instance)
        
        return self.success_response(
            data=serializer.data,
            message=f"{'Activated' if new_value else 'Deactivated'} successfully"
        )
    
    def post(self, request, *args, **kwargs):
        """Alternative method (POST) for activation toggle"""
        return self.patch(request, *args, **kwargs)


# ============================================================================
# Global Email Provider Activation
# ============================================================================

class GlobalEmailProviderActivationView(_BaseActivationToggleView):
    """
    Toggle activation status for global email providers.
    PATCH/POST: Toggle activated_by_tmd field
    """
    queryset = EmailProvider.objects.all()
    serializer_class = EmailProviderSerializer
    activation_field = 'activated_by_tmd'
    lookup_field = 'pk'


# ============================================================================
# Global Email Provider Default Toggle
# ============================================================================
class GlobalEmailProviderDefaultToggleView(CustomResponseMixin, generics.GenericAPIView):
    """
    Toggle the 'is_default' flag for global email providers.
    PATCH/POST: Set is_default to True. When set to True, the model.save()
    implementation will ensure only one provider remains default.
    """
    queryset = EmailProvider.objects.all()
    serializer_class = EmailProviderSerializer
    lookup_field = 'pk'
    permission_classes = [permissions.AllowAny]

    def patch(self, request, *args, **kwargs):
        """Set this provider as the default provider.

        This operation is idempotent and will NOT unset is_default if the
        provider is already default. To change the default provider, call
        this endpoint on another provider which will become the default.
        """
        instance = self.get_object()

        # If already default, do nothing (idempotent)
        if instance.is_default:
            serializer = self.get_serializer(instance)
            return self.success_response(
                data=serializer.data, 
                message="Provider is already the default."
            )

        # Otherwise mark as default; model.save() will unset other defaults
        instance.is_default = True
        instance.save(update_fields=['is_default', 'updated_at'])

        serializer = self.get_serializer(instance)
        return self.success_response(
            data=serializer.data, 
            message="Provider set as default successfully."
        )

    def post(self, request, *args, **kwargs):
        """Allow POST to behave the same as PATCH for convenience."""
        return self.patch(request, *args, **kwargs)


# ============================================================================
# Tenant Email Provider Activation
# ============================================================================

class TenantEmailProviderActivationView(_BaseActivationToggleView):
    """
    Toggle activation status for tenant email providers.
    PATCH/POST: Toggle is_enabled field
    """
    queryset = TenantEmailProvider.objects.all()
    serializer_class = TenantEmailProviderSerializer
    activation_field = 'is_enabled'
    lookup_field = 'pk'


# ============================================================================
# Tenant-Owned Email Provider Activation (NEW)
# ============================================================================

class TenantOwnEmailProviderActivationView(CustomResponseMixin, generics.GenericAPIView):
    """
    Toggle activation status for tenant-owned email providers.
    PATCH/POST: Toggle activated_by_td field
    
    Allows tenants to activate/deactivate their own email providers.
    Requires tenant_id query parameter for tenant isolation.
    
    Toggles the activated_by_td field (tenant-specific activation status).
    """
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """Get the appropriate serializer"""
        if TenantOwnEmailProviderSerializer:
            return TenantOwnEmailProviderSerializer
        return EmailProviderSerializer
    
    def get_queryset(self):
        """Get only tenant-owned providers for this tenant"""
        tenant_id = self.request.query_params.get('tenant_id')
        if not tenant_id:
            return EmailProvider.objects.none()
        
        return EmailProvider.objects.filter(
            tenant_id=tenant_id,
            is_global=False
        )
    
    def get_object(self):
        """Override to ensure tenant_id matches"""
        queryset = self.get_queryset()
        obj = generics.get_object_or_404(queryset, pk=self.kwargs['pk'])
        return obj
    
    def patch(self, request, *args, **kwargs):
        """Toggle the activation status (activated_by_td field)"""
        tenant_id = request.query_params.get('tenant_id')
        if not tenant_id:
            return self.error_response(
                message="tenant_id is required as query parameter",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        instance = self.get_object()
        
        # Toggle activated_by_td field (for tenant-specific providers)
        current_value = instance.activated_by_td
        new_value = not current_value

        instance.activated_by_td = new_value
        instance.save(update_fields=['activated_by_td', 'updated_at'])
        
        serializer = self.get_serializer(instance)
        
        return self.success_response(
            data=serializer.data,
            message=f"Provider {'activated' if new_value else 'deactivated'} successfully"
        )
    
    def post(self, request, *args, **kwargs):
        """Alternative method (POST) for activation toggle"""
        return self.patch(request, *args, **kwargs)


class TenantOwnEmailProviderSetDefaultView(CustomResponseMixin, generics.GenericAPIView):
    """
    Set a tenant-owned email provider as the default for the tenant.
    PATCH/POST: Set is_default to True for this provider only
    
    When set to True, the model.save() will ensure only one provider remains default.
    """
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """Get the appropriate serializer"""
        if TenantOwnEmailProviderSerializer:
            return TenantOwnEmailProviderSerializer
        return EmailProviderSerializer
    
    def get_queryset(self):
        """Get only tenant-owned providers for this tenant"""
        tenant_id = self.request.query_params.get('tenant_id')
        if not tenant_id:
            return EmailProvider.objects.none()
        
        return EmailProvider.objects.filter(
            tenant_id=tenant_id,
            is_global=False
        )
    
    def get_object(self):
        """Override to ensure tenant_id matches"""
        queryset = self.get_queryset()
        obj = generics.get_object_or_404(queryset, pk=self.kwargs['pk'])
        return obj
    
    def patch(self, request, *args, **kwargs):
        """Set this provider as default for the tenant"""
        tenant_id = request.query_params.get('tenant_id')
        if not tenant_id:
            return self.error_response(
                message="tenant_id is required as query parameter",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        instance = self.get_object()
        
        # If already default, return success (idempotent)
        if instance.is_default:
            serializer = self.get_serializer(instance)
            return self.success_response(
                data=serializer.data,
                message="Provider is already set as default"
            )
        
        # Set as default - model.save() will unset other defaults for this tenant
        instance.is_default = True
        instance.save(update_fields=['is_default', 'updated_at'])
        
        serializer = self.get_serializer(instance)
        
        return self.success_response(
            data=serializer.data,
            message="Provider set as default successfully"
        )
    
    def post(self, request, *args, **kwargs):
        """Allow POST to behave the same as PATCH for convenience"""
        return self.patch(request, *args, **kwargs)


# ============================================================================
# Tenant Email Configuration Activation
# ============================================================================

class TenantEmailConfigurationActivationView(_BaseActivationToggleView):
    """
    Toggle activation status for tenant email configurations.
    PATCH/POST: Toggle activated_by_tmd field
    """
    queryset = TenantEmailConfiguration.objects.all()
    serializer_class = TenantEmailConfigurationSerializer
    activation_field = 'activated_by_tmd'
    lookup_field = 'pk'


# ============================================================================
# Global Email Template Activation
# ============================================================================

class GlobalEmailTemplateActivationView(_BaseActivationToggleView):
    """
    Toggle activation status for global email templates.
    PATCH/POST: Toggle activated_by_tmd field
    """
    queryset = EmailTemplate.objects.filter(template_type=EmailTemplate.TemplateType.GLOBAL)
    serializer_class = GlobalEmailTemplateSerializer
    activation_field = 'activated_by_tmd'  # Using existing activation pattern
    lookup_field = 'pk'


# ============================================================================
# Tenant Email Template Activation  
# ============================================================================

class TenantEmailTemplateActivationView(_BaseActivationToggleView):
    """
    Toggle activation status for tenant email templates.
    PATCH/POST: Toggle activated_by_tmd field
    """
    queryset = EmailTemplate.objects.filter(template_type=EmailTemplate.TemplateType.TENANT)
    serializer_class = EmailTemplateSerializer
    activation_field = 'activated_by_td'
    lookup_field = 'pk'


# ============================================================================
# Global Automation Rule Activation
# ============================================================================

class GlobalAutomationRuleActivationView(_BaseActivationToggleView):
    """
    Toggle activation status for global automation rules.
    PATCH/POST: Toggle is_active field
    """
    queryset = AutomationRule.objects.filter(rule_scope=AutomationRule.RuleScope.GLOBAL)
    serializer_class = GlobalAutomationRuleSerializer
    activation_field = 'activated_by_tmd'
    lookup_field = 'pk'


# ============================================================================
# Tenant Automation Rule Activation
# ============================================================================

class TenantAutomationRuleActivationView(_BaseActivationToggleView):
    """
    Toggle activation status for tenant automation rules.
    PATCH/POST: Toggle is_active field (or activated_by_tmd)
    """
    queryset = AutomationRule.objects.filter(rule_scope=AutomationRule.RuleScope.TENANT)
    serializer_class = AutomationRuleSerializer
    activation_field = 'activated_by_td'  # Can also use 'activated_by_td' if needed
    lookup_field = 'pk'


# ============================================================================
# Legacy Activation Views (for backward compatibility)
# ============================================================================

class AutomationRuleActivationForTMDToggleView(_BaseActivationToggleView):
    """
    Legacy activation toggle view for automation rules.
    Maintained for backward compatibility.
    """
    queryset = AutomationRule.objects.filter(activated_by_root=True)
    serializer_class = AutomationRuleSerializer
    activation_field = 'activated_by_tmd'


class EmailTemplateActivationForTMDToggleView(_BaseActivationToggleView):
    """
    Legacy activation toggle view for email templates.
    Maintained for backward compatibility.
    """
    queryset = EmailTemplate.objects.filter(activated_by_root=True)
    serializer_class = EmailTemplateSerializer
    activation_field = 'activated_by_tmd'


class SMSConfigurationActivationForTMDToggleView(_BaseActivationToggleView):
    """
    Legacy activation toggle view for SMS configurations.
    Maintained for backward compatibility.
    """
    queryset = SMSConfigurationModel.objects.filter(activated_by_root=True)
    serializer_class = SMSConfigurationSerializer
    activation_field = 'activated_by_tmd'


class SMSTemplateActivationForTMDToggleView(_BaseActivationToggleView):
    """
    Legacy activation toggle view for SMS templates.
    Maintained for backward compatibility.
    """
    queryset = SMSTemplate.objects.filter(activated_by_root=True)
    serializer_class = SMSTemplateSerializer
    activation_field = 'activated_by_tmd'


# ============================================================================
# Additional Utility Views
# ============================================================================

class TenantEmailProviderSetPrimaryView(CustomResponseMixin, generics.GenericAPIView):
    """
    Set a tenant email provider as primary.
    This will unset any other primary providers for the same tenant.
    """
    permission_classes = [permissions.AllowAny]
    queryset = TenantEmailProvider.objects.all()
    serializer_class = TenantEmailProviderSerializer
    lookup_field = 'pk'
    
    def post(self, request, *args, **kwargs):
        """Set this provider as primary for the tenant"""
        instance = self.get_object()
        tenant_id = instance.tenant_id
        
        # Unset all other primary providers for this tenant
        TenantEmailProvider.objects.filter(
            tenant_id=tenant_id,
            is_primary=True
        ).exclude(pk=instance.pk).update(is_primary=False)
        
        # Set this provider as primary
        instance.is_primary = True
        instance.save(update_fields=['is_primary', 'updated_at'])
        
        serializer = self.get_serializer(instance)
        
        return self.success_response(
            data=serializer.data,
            message=f"Provider '{instance.provider.name}' set as primary for tenant"
        )
