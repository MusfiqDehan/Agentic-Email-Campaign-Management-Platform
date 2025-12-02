# Import all serializers from the base_serializers.py file (moved from original serializers.py)
from .base_serializers import (
    EmailTemplateSerializer,
    GlobalEmailTemplateSerializer,
    AutomationRuleSerializer,
    GlobalAutomationRuleSerializer,
    TriggerEmailSerializer,
    GlobalTriggerEmailSerializer,
    SMSConfigurationSerializer,
    SMSTemplateSerializer,
    TriggerSMSSerializer,
    TenantEmailConfigurationSerializer,
    EmailProviderSerializer,
    EnhancedEmailDeliveryLogSerializer,
    EnhancedTriggerEmailSerializer
)

# Import from enhanced_serializers.py in this directory
from .enhanced_serializers import (
    TenantEmailProviderSerializer,
    TenantOwnEmailProviderSerializer,
    EmailValidationSerializer,
    EmailQueueSerializer,
    EmailActionSerializer,
    EmailDeliveryLogSerializer,
    EnhancedAutomationRuleSerializer,
    TriggerEmailEnhancedSerializer
)

# Make all serializers available when importing from this package
__all__ = [
    'EmailTemplateSerializer',
    'GlobalEmailTemplateSerializer',
    'AutomationRuleSerializer',
    'GlobalAutomationRuleSerializer',
    'TriggerEmailSerializer',
    'GlobalTriggerEmailSerializer',
    'SMSConfigurationSerializer',
    'SMSTemplateSerializer',
    'TriggerSMSSerializer',
    'TenantEmailConfigurationSerializer',
    'EmailProviderSerializer',
    'EnhancedEmailDeliveryLogSerializer',
    'EnhancedTriggerEmailSerializer',
    'TenantEmailProviderSerializer',
    'TenantOwnEmailProviderSerializer',
    'EmailValidationSerializer',
    'EmailQueueSerializer',
    'EmailActionSerializer',
    'EmailDeliveryLogSerializer',
    'EnhancedAutomationRuleSerializer',
    'TriggerEmailEnhancedSerializer'
]
