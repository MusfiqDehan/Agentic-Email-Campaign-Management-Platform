"""
Views Package for Campaigns Application

Exports all views organized by purpose:
- Core views: Email templates, automation rules, SMS
- Campaign views: Campaigns, contacts, lists
- Admin views: Platform admin operations
- Enhanced views: Advanced provider and tracking features
"""

# Core views - Email Templates & Automation Rules
from .email_automation import (
    EmailTemplateListCreateView,
    EmailTemplateDetailView,
    AutomationRuleListCreateView,
    AutomationRuleDetailView,
    AutomationStatsView,
    EmailDispatchReportView,
)

# Core views - SMS
from .sms_automation import (
    SMSConfigurationListCreateView,
    SMSConfigurationDetailView,
    SMSTemplateListCreateView,
    SMSTemplateDetailView,
)

from .trigger_sms import (
    TriggerSMSView,
    TriggerWhatsAppView,
)

# Debug views
from .debug_views import (
    DebugAutoHealthCheckView,
)

# Campaign views (new)
from .campaign_views import (
    ContactListViewSet,
    ContactViewSet,
    CampaignViewSet,
    UnsubscribeView,
    GDPRForgetView,
)

# Admin views (new)
from .admin_views import (
    AdminEmailProviderViewSet,
    AdminOrganizationConfigViewSet,
    IsPlatformAdmin,
)

# Activation views (simplified - is_active/is_published toggles)
from .activation_views import *

__all__ = [
    # Email Template Views
    'EmailTemplateListCreateView',
    'EmailTemplateDetailView',
    
    # Automation Rule Views
    'AutomationRuleListCreateView',
    'AutomationRuleDetailView',
    
    # Stats Views
    'AutomationStatsView',
    'EmailDispatchReportView',
    
    # SMS Views
    'SMSConfigurationListCreateView',
    'SMSConfigurationDetailView',
    'SMSTemplateListCreateView',
    'SMSTemplateDetailView',
    'TriggerSMSView',
    'TriggerWhatsAppView',
    
    # Debug Views
    'DebugAutoHealthCheckView',
    
    # Campaign Views (new)
    'ContactListViewSet',
    'ContactViewSet',
    'CampaignViewSet',
    'UnsubscribeView',
    'GDPRForgetView',
    
    # Admin Views (new)
    'AdminEmailProviderViewSet',
    'AdminOrganizationConfigViewSet',
    'IsPlatformAdmin',
]
