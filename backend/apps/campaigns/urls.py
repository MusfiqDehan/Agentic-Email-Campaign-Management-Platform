"""
URL Configuration for Campaigns Application

Simplified URL structure organized into clear sections:
1. Campaign Management (Campaigns, Contacts, Lists)
2. Email Configuration (Templates, Providers)
3. Automation Rules
4. Email Delivery & Tracking
5. SMS/WhatsApp Automation
6. Admin/Platform Operations
7. Public Endpoints (Unsubscribe, Tracking)

All endpoints use APIView for explicit control.
"""

from django.urls import path
# Import campaign views
from .views import (
    # Contact List Views
    ContactListListCreateView,
    ContactListDetailView,
    ContactListRefreshStatsView,
    
    # Contact Views
    ContactListView as ContactsListView,  # Renamed to avoid confusion
    ContactDetailView,
    ContactBulkImportView,
    
    # Campaign Views
    CampaignListCreateView,
    CampaignDetailView,
    CampaignLaunchView,
    CampaignScheduleView,
    CampaignPauseView,
    CampaignResumeView,
    CampaignCancelView,
    CampaignResetView,
    CampaignPreviewView,
    CampaignTestSendView,
    CampaignDuplicateView,
    CampaignAnalyticsView,
    CampaignRefreshStatsView,
    
    # Public Views
    UnsubscribeView,
    GDPRForgetView,
    
    # Admin Views
    AdminEmailProviderListCreateView,
    AdminEmailProviderDetailView,
    AdminEmailProviderSetDefaultView,
    AdminEmailProviderHealthCheckView,
    AdminEmailProviderTestSendView,
    AdminOrganizationConfigListView,
    AdminOrganizationConfigDetailView,
    AdminOrganizationSuspendView,
    AdminOrganizationUnsuspendView,
    AdminOrganizationUpgradePlanView,
    AdminPlatformStatsView,
    IsPlatformAdmin,
    
    # Email Template Views
    EmailTemplateListCreateView,
    EmailTemplateDetailView,
    
    # Automation Rule Views
    AutomationRuleListCreateView,
    AutomationRuleDetailView,
    
    # SMS Views
    SMSConfigurationListCreateView,
    SMSConfigurationDetailView,
    SMSTemplateListCreateView,
    SMSTemplateDetailView,
    TriggerSMSView,
    TriggerWhatsAppView,
    
    # Stats & Debug
    AutomationStatsView,
    EmailDispatchReportView,
    DebugAutoHealthCheckView,
    
    # Variable Views - Template Personalization
    VariableListView,
    VariableExtractView,
    VariableValidateView,
    CustomFieldSchemaView,
    VariablePreviewView,

    GenerateEmailContentAIView
)

# Import enhanced views
from .views.enhanced_views import (
    # Organization Email Configuration Views
    OrganizationEmailConfigurationListCreateView,
    OrganizationEmailConfigurationDetailView,
    OrganizationEmailConfigurationResetUsageView,
    OrganizationEmailConfigurationVerifyDomainView,
    OrganizationEmailConfigurationUsageStatsView,
    
    # Email Provider Views (Shared/Platform Providers - read-only for org users)
    EmailProviderListCreateView,
    EmailProviderDetailView,
    EmailProviderHealthCheckView,
    EmailProviderTestSendView,
    
    # Organization Email Provider Views (links org to providers)
    OrganizationEmailProviderListCreateView,
    OrganizationEmailProviderDetailView,

    # Organization Own Email Provider Views (org-owned providers)
    OrganizationOwnEmailProviderListCreateView,
    OrganizationOwnEmailProviderDetailView,
    OrganizationOwnEmailProviderHealthCheckView,
    OrganizationOwnEmailProviderTestSendView,
    
    # Email Delivery Log Views
    EmailDeliveryLogListView,
    EmailDeliveryLogDetailView,
    EmailDeliveryLogResendView,
    EmailDeliveryLogForwardView,
    EmailDeliveryLogAnalyticsView,
    
    # Email Validation Views
    EmailValidationListView,
    EmailValidationDetailView,
    
    # Email Queue Views
    EmailQueueListView,
    EmailQueueDetailView,
    EmailQueueProcessView,
    
    # Email Action Views
    EmailActionListView,
    EmailActionDetailView,
    
    # Enhanced Trigger View
    EnhancedTriggerEmailView,
)


urlpatterns = [
    # ========================================================================
    # SECTION 1: CAMPAIGN MANAGEMENT
    # ========================================================================
    
    # Campaigns
    path('', CampaignListCreateView.as_view(), name='campaign-list-create'),
    path('<uuid:pk>/', CampaignDetailView.as_view(), name='campaign-detail'),
    path('<uuid:pk>/launch/', CampaignLaunchView.as_view(), name='campaign-launch'),
    path('<uuid:pk>/schedule/', CampaignScheduleView.as_view(), name='campaign-schedule'),
    path('<uuid:pk>/pause/', CampaignPauseView.as_view(), name='campaign-pause'),
    path('<uuid:pk>/resume/', CampaignResumeView.as_view(), name='campaign-resume'),
    path('<uuid:pk>/cancel/', CampaignCancelView.as_view(), name='campaign-cancel'),
    path('<uuid:pk>/reset/', CampaignResetView.as_view(), name='campaign-reset'),
    path('<uuid:pk>/preview/', CampaignPreviewView.as_view(), name='campaign-preview'),
    path('<uuid:pk>/test-send/', CampaignTestSendView.as_view(), name='campaign-test-send'),
    path('<uuid:pk>/duplicate/', CampaignDuplicateView.as_view(), name='campaign-duplicate'),
    path('<uuid:pk>/analytics/', CampaignAnalyticsView.as_view(), name='campaign-analytics'),
    path('<uuid:pk>/refresh-stats/', CampaignRefreshStatsView.as_view(), name='campaign-refresh-stats'),
    
    # Contacts
    path('contacts/', ContactsListView.as_view(), name='contact-list-create'),
    path('contacts/bulk/', ContactBulkImportView.as_view(), name='contact-bulk-import'),
    path('contacts/<uuid:pk>/', ContactDetailView.as_view(), name='contact-detail'),
    
    # Contact Lists
    path('contact-lists/', ContactListListCreateView.as_view(), name='contact-list-list-create'),
    path('contact-lists/<uuid:pk>/', ContactListDetailView.as_view(), name='contact-list-detail'),
    path('contact-lists/<uuid:pk>/refresh-stats/', ContactListRefreshStatsView.as_view(), name='contact-list-refresh-stats'),
    
    # ========================================================================
    # SECTION 2: EMAIL CONFIGURATION
    # Organization-scoped email settings
    # ========================================================================
    
    # Email Templates
    path('templates/', EmailTemplateListCreateView.as_view(), name='email-template-list-create'),
    path('templates/<uuid:pk>/', EmailTemplateDetailView.as_view(), name='email-template-detail'),
    
    # Organization Email Configuration
    path('config/', OrganizationEmailConfigurationListCreateView.as_view(), name='org-email-config-list'),
    path('config/<uuid:pk>/', OrganizationEmailConfigurationDetailView.as_view(), name='org-email-config-detail'),
    path('config/<uuid:pk>/reset-usage/', OrganizationEmailConfigurationResetUsageView.as_view(), name='org-email-config-reset-usage'),
    path('config/<uuid:pk>/verify-domain/', OrganizationEmailConfigurationVerifyDomainView.as_view(), name='org-email-config-verify-domain'),
    path('config/usage-stats/', OrganizationEmailConfigurationUsageStatsView.as_view(), name='org-email-config-usage-stats'),
    
    # Organization Email Providers (links org to shared/platform providers)
    path('providers/', OrganizationEmailProviderListCreateView.as_view(), name='org-email-provider-list-create'),
    path('providers/<uuid:pk>/', OrganizationEmailProviderDetailView.as_view(), name='org-email-provider-detail'),

    # Organization Own Email Providers (org-owned providers created by org admins)
    path('own-providers/', OrganizationOwnEmailProviderListCreateView.as_view(), name='org-own-provider-list-create'),
    path('own-providers/<uuid:pk>/', OrganizationOwnEmailProviderDetailView.as_view(), name='org-own-provider-detail'),
    path('own-providers/<uuid:pk>/health-check/', OrganizationOwnEmailProviderHealthCheckView.as_view(), name='org-own-provider-health-check'),
    path('own-providers/<uuid:pk>/test-send/', OrganizationOwnEmailProviderTestSendView.as_view(), name='org-own-provider-test-send'),
    
    # Shared Email Providers (read-only for regular users)
    path('shared-providers/', EmailProviderListCreateView.as_view(), name='shared-email-provider-list'),
    path('shared-providers/<uuid:pk>/', EmailProviderDetailView.as_view(), name='shared-email-provider-detail'),
    path('shared-providers/<uuid:pk>/health-check/', EmailProviderHealthCheckView.as_view(), name='shared-email-provider-health-check'),
    
    # ========================================================================
    # SECTION 3: AUTOMATION RULES
    # Organization-scoped automation rules
    # ========================================================================
    
    path('rules/', AutomationRuleListCreateView.as_view(), name='automation-rule-list-create'),
    path('rules/<uuid:pk>/', AutomationRuleDetailView.as_view(), name='automation-rule-detail'),
    
    # ========================================================================
    # SECTION 4: EMAIL DELIVERY & TRACKING
    # ========================================================================
    
    # Trigger Email
    path('trigger/email/', EnhancedTriggerEmailView.as_view(), name='trigger-email'),
    path('trigger/email/<uuid:rule_id>/', EnhancedTriggerEmailView.as_view(), name='trigger-email-by-rule'),
    
    # Email Queue
    path('queue/', EmailQueueListView.as_view(), name='email-queue-list'),
    path('queue/<uuid:pk>/', EmailQueueDetailView.as_view(), name='email-queue-detail'),
    path('queue/process/', EmailQueueProcessView.as_view(), name='email-queue-process'),
    
    # Delivery Logs
    path('logs/', EmailDeliveryLogListView.as_view(), name='email-delivery-log-list'),
    path('logs/<uuid:pk>/', EmailDeliveryLogDetailView.as_view(), name='email-delivery-log-detail'),
    path('logs/<uuid:pk>/resend/', EmailDeliveryLogResendView.as_view(), name='email-delivery-log-resend'),
    path('logs/<uuid:pk>/forward/', EmailDeliveryLogForwardView.as_view(), name='email-delivery-log-forward'),
    path('logs/analytics/', EmailDeliveryLogAnalyticsView.as_view(), name='email-delivery-log-analytics'),
    
    # Email Validation
    path('validations/', EmailValidationListView.as_view(), name='email-validation-list'),
    path('validations/<uuid:pk>/', EmailValidationDetailView.as_view(), name='email-validation-detail'),
    
    # Email Actions
    path('actions/', EmailActionListView.as_view(), name='email-action-list'),
    path('actions/<uuid:pk>/', EmailActionDetailView.as_view(), name='email-action-detail'),
    
    # ========================================================================
    # SECTION 5: SMS & WHATSAPP AUTOMATION
    # ========================================================================
    
    # SMS Configuration
    path('sms/configs/', SMSConfigurationListCreateView.as_view(), name='sms-config-list-create'),
    path('sms/configs/<uuid:pk>/', SMSConfigurationDetailView.as_view(), name='sms-config-detail'),
    
    # SMS Templates
    path('sms/templates/', SMSTemplateListCreateView.as_view(), name='sms-template-list-create'),
    path('sms/templates/<uuid:pk>/', SMSTemplateDetailView.as_view(), name='sms-template-detail'),
    
    # Trigger SMS/WhatsApp
    path('trigger/sms/', TriggerSMSView.as_view(), name='trigger-sms'),
    path('trigger/sms/<uuid:rule_id>/', TriggerSMSView.as_view(), name='trigger-sms-by-rule'),
    path('trigger/whatsapp/', TriggerWhatsAppView.as_view(), name='trigger-whatsapp'),
    path('trigger/whatsapp/<uuid:rule_id>/', TriggerWhatsAppView.as_view(), name='trigger-whatsapp-by-rule'),
    
    # ========================================================================
    # SECTION 6: ADMIN/PLATFORM OPERATIONS
    # Requires platform admin permissions
    # ========================================================================
    
    # Admin Email Providers
    path('admin/providers/', AdminEmailProviderListCreateView.as_view(), name='admin-provider-list-create'),
    path('admin/providers/<uuid:pk>/', AdminEmailProviderDetailView.as_view(), name='admin-provider-detail'),
    path('admin/providers/<uuid:pk>/set-default/', AdminEmailProviderSetDefaultView.as_view(), name='admin-provider-set-default'),
    path('admin/providers/<uuid:pk>/health-check/', AdminEmailProviderHealthCheckView.as_view(), name='admin-provider-health-check'),
    path('admin/providers/<uuid:pk>/test-send/', AdminEmailProviderTestSendView.as_view(), name='admin-provider-test-send'),
    
    # Admin Organization Configs
    path('admin/organizations/', AdminOrganizationConfigListView.as_view(), name='admin-org-config-list'),
    path('admin/organizations/<uuid:pk>/', AdminOrganizationConfigDetailView.as_view(), name='admin-org-config-detail'),
    path('admin/organizations/<uuid:pk>/suspend/', AdminOrganizationSuspendView.as_view(), name='admin-org-suspend'),
    path('admin/organizations/<uuid:pk>/unsuspend/', AdminOrganizationUnsuspendView.as_view(), name='admin-org-unsuspend'),
    path('admin/organizations/<uuid:pk>/upgrade-plan/', AdminOrganizationUpgradePlanView.as_view(), name='admin-org-upgrade-plan'),
    
    # Admin Platform Stats
    path('admin/stats/', AdminPlatformStatsView.as_view(), name='admin-platform-stats'),
    
    # ========================================================================
    # SECTION 7: PUBLIC ENDPOINTS
    # ========================================================================
    
    path('unsubscribe/', UnsubscribeView.as_view(), name='unsubscribe'),
    path('gdpr/forget/', GDPRForgetView.as_view(), name='gdpr-forget'),
    
    # ========================================================================
    # SECTION 8: MONITORING & DEBUGGING
    # ========================================================================
    
    path('stats/', AutomationStatsView.as_view(), name='automation-stats'),
    path('dispatches/', EmailDispatchReportView.as_view(), name='email-dispatch-report'),
    path('health/', DebugAutoHealthCheckView.as_view(), name='health-check'),
    
    # ========================================================================
    # SECTION 9: TEMPLATE VARIABLES
    # For autocomplete and template personalization
    # ========================================================================
    
    path('variables/', VariableListView.as_view(), name='variable-list'),
    path('variables/extract/', VariableExtractView.as_view(), name='variable-extract'),
    path('variables/validate/', VariableValidateView.as_view(), name='variable-validate'),
    path('variables/preview/', VariablePreviewView.as_view(), name='variable-preview'),
    path('variables/schema/', CustomFieldSchemaView.as_view(), name='custom-field-schema'),

    path('ai/generate/email/content/', GenerateEmailContentAIView.as_view(), name='generate-email-content-ai'),
]
