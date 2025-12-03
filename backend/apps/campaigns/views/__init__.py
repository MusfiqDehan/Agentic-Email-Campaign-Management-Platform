"""
Views Package for Campaigns Application

Exports all views organized by purpose:
- Core views: Email templates, automation rules, SMS
- Campaign views: Campaigns, contacts, lists
- Admin views: Platform admin operations
- Enhanced views: Advanced provider and tracking features

All views use APIView for explicit control over request handling.
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

# Campaign views - Contact Lists
from .campaign_views import (
    ContactListListCreateView,
    ContactListDetailView,
    ContactListRefreshStatsView,
)

# Campaign views - Contacts
from .campaign_views import (
    ContactListView,
    ContactDetailView,
    ContactBulkImportView,
)

# Campaign views - Campaigns
from .campaign_views import (
    CampaignListCreateView,
    CampaignDetailView,
    CampaignLaunchView,
    CampaignScheduleView,
    CampaignPauseView,
    CampaignResumeView,
    CampaignCancelView,
    CampaignPreviewView,
    CampaignTestSendView,
    CampaignDuplicateView,
    CampaignAnalyticsView,
    CampaignRefreshStatsView,
)

# Campaign views - Public
from .campaign_views import (
    UnsubscribeView,
    GDPRForgetView,
)

# Admin views - Providers
from .admin_views import (
    IsPlatformAdmin,
    AdminEmailProviderListCreateView,
    AdminEmailProviderDetailView,
    AdminEmailProviderSetDefaultView,
    AdminEmailProviderHealthCheckView,
    AdminEmailProviderTestSendView,
)

# Admin views - Organizations
from .admin_views import (
    AdminOrganizationConfigListView,
    AdminOrganizationConfigDetailView,
    AdminOrganizationSuspendView,
    AdminOrganizationUnsuspendView,
    AdminOrganizationUpgradePlanView,
    AdminPlatformStatsView,
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
    
    # Contact List Views
    'ContactListListCreateView',
    'ContactListDetailView',
    'ContactListRefreshStatsView',
    
    # Contact Views
    'ContactListView',
    'ContactDetailView',
    'ContactBulkImportView',
    
    # Campaign Views
    'CampaignListCreateView',
    'CampaignDetailView',
    'CampaignLaunchView',
    'CampaignScheduleView',
    'CampaignPauseView',
    'CampaignResumeView',
    'CampaignCancelView',
    'CampaignPreviewView',
    'CampaignTestSendView',
    'CampaignDuplicateView',
    'CampaignAnalyticsView',
    'CampaignRefreshStatsView',
    
    # Public Views
    'UnsubscribeView',
    'GDPRForgetView',
    
    # Admin Views - Providers
    'IsPlatformAdmin',
    'AdminEmailProviderListCreateView',
    'AdminEmailProviderDetailView',
    'AdminEmailProviderSetDefaultView',
    'AdminEmailProviderHealthCheckView',
    'AdminEmailProviderTestSendView',
    
    # Admin Views - Organizations
    'AdminOrganizationConfigListView',
    'AdminOrganizationConfigDetailView',
    'AdminOrganizationSuspendView',
    'AdminOrganizationUnsuspendView',
    'AdminOrganizationUpgradePlanView',
    'AdminPlatformStatsView',
]
