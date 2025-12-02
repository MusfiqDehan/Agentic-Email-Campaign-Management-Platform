"""
Serializers Package for Campaigns Application

Exports all serializers organized by purpose:
- Base serializers: Core models (templates, rules, SMS)
- Enhanced serializers: Provider and tracking related
- Campaign serializers: Campaign management features
"""

# Import from base_serializers.py
from .base_serializers import (
    # Email Templates
    EmailTemplateSerializer,
    
    # Automation Rules
    AutomationRuleSerializer,
    
    # Email Triggering
    TriggerEmailSerializer,
    EnhancedTriggerEmailSerializer,
    
    # SMS
    SMSConfigurationSerializer,
    SMSTemplateSerializer,
    TriggerSMSSerializer,
    
    # Organization Config
    OrganizationEmailConfigurationSerializer,
    
    # Providers
    EmailProviderSerializer,
    
    # Delivery Logs
    EnhancedEmailDeliveryLogSerializer,
)

# Import from enhanced_serializers.py
from .enhanced_serializers import (
    # Organization Email Provider
    TenantEmailProviderSerializer as OrganizationEmailProviderSerializer,
    
    # Email Tracking
    EmailValidationSerializer,
    EmailQueueSerializer,
    EmailActionSerializer,
    EmailDeliveryLogSerializer,
    
    # Enhanced Rule
    EnhancedAutomationRuleSerializer,
    TriggerEmailEnhancedSerializer,
)

# Import from campaign_serializers.py
from .campaign_serializers import (
    # Contact Lists
    ContactListSerializer,
    ContactListSummarySerializer,
    
    # Contacts
    ContactSerializer,
    ContactMinimalSerializer,
    BulkContactCreateSerializer,
    
    # Campaigns
    CampaignSerializer,
    CampaignListSerializer,
    CampaignPreviewSerializer,
    CampaignTestSendSerializer,
    CampaignDuplicateSerializer,
    CampaignScheduleSerializer,
    CampaignAnalyticsSerializer,
    
    # Public Actions
    UnsubscribeSerializer,
    GDPRForgetSerializer,
)

# Backward compatibility aliases (deprecated - use new names)
TenantEmailConfigurationSerializer = OrganizationEmailConfigurationSerializer
TenantEmailProviderSerializer = OrganizationEmailProviderSerializer

__all__ = [
    # Base serializers
    'EmailTemplateSerializer',
    'AutomationRuleSerializer',
    'TriggerEmailSerializer',
    'EnhancedTriggerEmailSerializer',
    'SMSConfigurationSerializer',
    'SMSTemplateSerializer',
    'TriggerSMSSerializer',
    'OrganizationEmailConfigurationSerializer',
    'EmailProviderSerializer',
    'EnhancedEmailDeliveryLogSerializer',
    
    # Enhanced serializers
    'OrganizationEmailProviderSerializer',
    'EmailValidationSerializer',
    'EmailQueueSerializer',
    'EmailActionSerializer',
    'EmailDeliveryLogSerializer',
    'EnhancedAutomationRuleSerializer',
    'TriggerEmailEnhancedSerializer',
    
    # Campaign serializers
    'ContactListSerializer',
    'ContactListSummarySerializer',
    'ContactSerializer',
    'ContactMinimalSerializer',
    'BulkContactCreateSerializer',
    'CampaignSerializer',
    'CampaignListSerializer',
    'CampaignPreviewSerializer',
    'CampaignTestSendSerializer',
    'CampaignDuplicateSerializer',
    'CampaignScheduleSerializer',
    'CampaignAnalyticsSerializer',
    'UnsubscribeSerializer',
    'GDPRForgetSerializer',
    
    # Backward compatibility (deprecated)
    'TenantEmailConfigurationSerializer',
    'TenantEmailProviderSerializer',
]
