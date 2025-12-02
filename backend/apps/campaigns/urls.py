"""
URL Configuration for Automation Rule Application

This file organizes all email automation endpoints into clear sections:
1. Global Email Automation (global resources shared across tenants)
2. Tenant Email Automation (tenant-specific resources)
3. Email Providers (global and tenant-specific)
4. Triggering & Execution
5. Monitoring & Analytics
6. Legacy Endpoints (maintained for backward compatibility)
"""

from django.urls import path
from .views import (
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
    
    # Trigger Views
    TriggerEmailView,
    
    # Stats & Reports
    AutomationStatsView,
    EmailDispatchReportView,
    DebugAutoHealthCheckView,
    
    # Global Email Views
    GlobalEmailTriggerView,
    GlobalAutomationRuleListView,
    GlobalAutomationRuleDetailView,
    GlobalEmailTemplateListView,
    GlobalEmailTemplateDetailView,
    GlobalEmailProviderListView,
    GlobalEmailAnalyticsView,
    GlobalEmailHealthCheckView,
    
    # Activation Views (New Unified System)
    GlobalEmailProviderActivationView,
    GlobalEmailProviderDefaultToggleView,
    TenantEmailProviderActivationView,
    TenantEmailProviderSetPrimaryView,
    TenantOwnEmailProviderActivationView,
    TenantOwnEmailProviderSetDefaultView,
    TenantEmailConfigurationActivationView,
    GlobalEmailTemplateActivationView,
    TenantEmailTemplateActivationView,
    GlobalAutomationRuleActivationView,
    TenantAutomationRuleActivationView,
    
    # Legacy Activation Views (Backward Compatibility)
    AutomationRuleActivationForTMDToggleView,
    EmailTemplateActivationForTMDToggleView,
    SMSConfigurationActivationForTMDToggleView,
    SMSTemplateActivationForTMDToggleView,
)

# Import enhanced views
from .views.enhanced_views import (
    # Tenant Email Configuration Views
    TenantEmailConfigurationListCreateView,
    TenantEmailConfigurationDetailView,
    TenantEmailConfigurationResetUsageView,
    TenantEmailConfigurationVerifyDomainView,
    TenantEmailConfigurationUsageStatsView,
    
    # Email Provider Views
    EmailProviderListCreateView,
    EmailProviderDetailView,
    EmailProviderHealthCheckView,
    EmailProviderTestSendView,
    
    # Tenant-Owned Email Provider Views (NEW)
    TenantOwnEmailProviderListCreateView,
    TenantOwnEmailProviderDetailView,
    TenantOwnEmailProviderHealthCheckView,
    
    # Email Delivery Log Views
    EmailDeliveryLogListView,
    EmailDeliveryLogDetailView,
    EmailDeliveryLogResendView,
    EmailDeliveryLogForwardView,
    EmailDeliveryLogAnalyticsView,
    
    # Tenant Email Provider Views
    TenantEmailProviderListCreateView,
    TenantEmailProviderDetailView,
    
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
    # SECTION 1: GLOBAL EMAIL AUTOMATION
    # Resources shared across all tenants
    # ========================================================================
    
    # Global Email Providers (Convenience endpoints - same as /email/providers/)
    path('global/providers/', GlobalEmailProviderListView.as_view(), name='global-email-provider-list'),
    
    # Global Email Templates
    path('global/templates/', GlobalEmailTemplateListView.as_view(), name='global-email-template-list-create'),
    path('global/templates/<uuid:pk>/', GlobalEmailTemplateDetailView.as_view(), name='global-email-template-detail'),
    path('global/templates/<uuid:pk>/activate/', GlobalEmailTemplateActivationView.as_view(), name='global-email-template-activate'),
    
    # Global Automation Rules
    path('global/rules/', GlobalAutomationRuleListView.as_view(), name='global-automation-rule-list-create'),
    path('global/rules/<uuid:pk>/', GlobalAutomationRuleDetailView.as_view(), name='global-automation-rule-detail'),
    path('global/rules/<uuid:pk>/activate/', GlobalAutomationRuleActivationView.as_view(), name='global-automation-rule-activate'),
    
    # Global Email Triggering & Analytics
    path('global/trigger-email/', GlobalEmailTriggerView.as_view(), name='trigger-global-email'),
    path('global/analytics/', GlobalEmailAnalyticsView.as_view(), name='global-email-analytics'),
    path('global/health/', GlobalEmailHealthCheckView.as_view(), name='global-email-health'),
    
    # ========================================================================
    # SECTION 2: TENANT EMAIL AUTOMATION
    # Tenant-specific email resources
    # ========================================================================
    
    # Tenant Email Templates
    path('tenant/templates/', EmailTemplateListCreateView.as_view(), name='tenant-email-template-list-create'),
    path('tenant/templates/<uuid:pk>/', EmailTemplateDetailView.as_view(), name='tenant-email-template-detail'),
    path('tenant/templates/<uuid:pk>/activate/', TenantEmailTemplateActivationView.as_view(), name='tenant-email-template-activate'),
    
    # Tenant Automation Rules
    path('tenant/rules/', AutomationRuleListCreateView.as_view(), name='tenant-automation-rule-list-create'),
    path('tenant/rules/<uuid:pk>/', AutomationRuleDetailView.as_view(), name='tenant-automation-rule-detail'),
    path('tenant/rules/<uuid:pk>/activate/', TenantAutomationRuleActivationView.as_view(), name='tenant-automation-rule-activate'),
    
    # Tenant Email Configuration
    path('tenant/configs/', TenantEmailConfigurationListCreateView.as_view(), name='tenant-email-config-list-create'),
    path('tenant/configs/<uuid:pk>/', TenantEmailConfigurationDetailView.as_view(), name='tenant-email-config-detail'),
    path('tenant/configs/<uuid:pk>/activate/', TenantEmailConfigurationActivationView.as_view(), name='tenant-email-config-activate'),
    path('tenant/configs/<uuid:pk>/reset-usage/', TenantEmailConfigurationResetUsageView.as_view(), name='tenant-email-config-reset-usage'),
    path('tenant/configs/<uuid:pk>/verify-domain/', TenantEmailConfigurationVerifyDomainView.as_view(), name='tenant-email-config-verify-domain'),
    path('tenant/configs/usage-stats/', TenantEmailConfigurationUsageStatsView.as_view(), name='tenant-email-config-usage-stats'),
    
    # Tenant Email Providers (Bindings to global providers)
    path('tenant/providers/', TenantEmailProviderListCreateView.as_view(), name='tenant-email-provider-list-create'),
    path('tenant/providers/<uuid:pk>/', TenantEmailProviderDetailView.as_view(), name='tenant-email-provider-detail'),
    path('tenant/providers/<uuid:pk>/activate/', TenantEmailProviderActivationView.as_view(), name='tenant-email-provider-activate'),
    path('tenant/providers/<uuid:pk>/set-primary/', TenantEmailProviderSetPrimaryView.as_view(), name='tenant-email-provider-set-primary'),
    
    # Tenant-Owned Email Providers (NEW - allows tenants to create their own providers)
    path('tenant/own-providers/', TenantOwnEmailProviderListCreateView.as_view(), name='tenant-own-email-provider-list-create'),
    path('tenant/own-providers/<uuid:pk>/', TenantOwnEmailProviderDetailView.as_view(), name='tenant-own-email-provider-detail'),
    path('tenant/own-providers/<uuid:pk>/health-check/', TenantOwnEmailProviderHealthCheckView.as_view(), name='tenant-own-email-provider-health-check'),
    path('tenant/own-providers/<uuid:pk>/activate/', TenantOwnEmailProviderActivationView.as_view(), name='tenant-own-email-provider-activate'),
    path('tenant/own-providers/<uuid:pk>/set-default/', TenantOwnEmailProviderSetDefaultView.as_view(), name='tenant-own-email-provider-set-default'),
    
    # ========================================================================
    # SECTION 3: EMAIL PROVIDERS (Global Provider Management)
    # Manage global email providers (SES, SMTP, SendGrid, etc.)
    # ========================================================================
    
    path('email/providers/', EmailProviderListCreateView.as_view(), name='email-provider-list-create'),
    path('email/providers/<uuid:pk>/', EmailProviderDetailView.as_view(), name='email-provider-detail'),
    path('email/providers/<uuid:pk>/activate/', GlobalEmailProviderActivationView.as_view(), name='email-provider-activate'),
    path('email/providers/<uuid:pk>/set-default/', GlobalEmailProviderDefaultToggleView.as_view(), name='email-provider-set-default'),
    path('email/providers/<uuid:pk>/health-check/', EmailProviderHealthCheckView.as_view(), name='email-provider-health-check'),
    path('email/providers/<uuid:pk>/test-send/', EmailProviderTestSendView.as_view(), name='email-provider-test-send'),
    
    # ========================================================================
    # SECTION 4: EMAIL TRIGGERING & EXECUTION
    # Send emails, process queues, and track delivery
    # ========================================================================
    
    # Email Triggering
    path('trigger/email/', TriggerEmailView.as_view(), name='trigger-email'),
    path('trigger/email/<uuid:rule_id>/', TriggerEmailView.as_view(), name='trigger-email-with-id'),
    path('trigger/enhanced-email/', EnhancedTriggerEmailView.as_view(), name='enhanced-trigger-email'),
    path('trigger/enhanced-email/<uuid:rule_id>/', EnhancedTriggerEmailView.as_view(), name='enhanced-trigger-email-with-id'),
    
    # Email Queue Management
    path('email/queues/', EmailQueueListView.as_view(), name='email-queue-list'),
    path('email/queues/<uuid:pk>/', EmailQueueDetailView.as_view(), name='email-queue-detail'),
    path('email/queues/process/', EmailQueueProcessView.as_view(), name='email-queue-process'),
    
    # Email Delivery Tracking
    path('email/delivery/logs/', EmailDeliveryLogListView.as_view(), name='email-delivery-log-list'),
    path('email/delivery/logs/<uuid:pk>/', EmailDeliveryLogDetailView.as_view(), name='email-delivery-log-detail'),
    path('email/delivery/logs/<uuid:pk>/resend/', EmailDeliveryLogResendView.as_view(), name='email-delivery-log-resend'),
    path('email/delivery/logs/<uuid:pk>/forward/', EmailDeliveryLogForwardView.as_view(), name='email-delivery-log-forward'),
    path('email/delivery/logs/analytics/', EmailDeliveryLogAnalyticsView.as_view(), name='email-delivery-log-analytics'),
    
    # Email Validation
    path('email/validations/', EmailValidationListView.as_view(), name='email-validation-list'),
    path('email/validations/<uuid:pk>/', EmailValidationDetailView.as_view(), name='email-validation-detail'),
    
    # Email Actions
    path('email/actions/', EmailActionListView.as_view(), name='email-action-list'),
    path('email/actions/<uuid:pk>/', EmailActionDetailView.as_view(), name='email-action-detail'),
    
    # ========================================================================
    # SECTION 5: SMS & WHATSAPP AUTOMATION
    # SMS and WhatsApp messaging automation
    # ========================================================================
    
    # SMS Configuration
    path('sms/configs/', SMSConfigurationListCreateView.as_view(), name='sms-config-list-create'),
    path('sms/configs/<uuid:pk>/', SMSConfigurationDetailView.as_view(), name='sms-config-detail'),
    path('sms/configs/<uuid:pk>/activation/', SMSConfigurationActivationForTMDToggleView.as_view(), name='sms-config-activation'),
    
    # SMS Templates
    path('sms/templates/', SMSTemplateListCreateView.as_view(), name='sms-template-list-create'),
    path('sms/templates/<uuid:pk>/', SMSTemplateDetailView.as_view(), name='sms-template-detail'),
    path('sms/templates/<uuid:pk>/activation/', SMSTemplateActivationForTMDToggleView.as_view(), name='sms-template-activation'),
    
    # SMS Triggering
    path('trigger/sms/', TriggerSMSView.as_view(), name='trigger-sms-no-id'),
    path('trigger/sms/<uuid:rule_id>/', TriggerSMSView.as_view(), name='trigger-sms'),
    
    # WhatsApp Triggering
    path('trigger/whatsapp/', TriggerWhatsAppView.as_view(), name='trigger-whatsapp-no-id'),
    path('trigger/whatsapp/<uuid:rule_id>/', TriggerWhatsAppView.as_view(), name='trigger-whatsapp'),
    
    # ========================================================================
    # SECTION 6: MONITORING, ANALYTICS & DEBUGGING
    # System health, stats, and debugging endpoints
    # ========================================================================
    
    path('stats/', AutomationStatsView.as_view(), name='automation-stats'),
    path('email/dispatches/', EmailDispatchReportView.as_view(), name='email-dispatch-report'),
    path('debug/auto-health-check/', DebugAutoHealthCheckView.as_view(), name='debug-auto-health-check'),
    
    # ========================================================================
    # SECTION 7: LEGACY ENDPOINTS (Backward Compatibility)
    # Maintained for backward compatibility - DO NOT USE IN NEW CODE
    # ========================================================================
    
    # Legacy Automation Rule Endpoints
    path('rules/', AutomationRuleListCreateView.as_view(), name='automation-rule-list-create'),
    path('rules/<uuid:pk>/', AutomationRuleDetailView.as_view(), name='automation-rule-detail'),
    path('rules/<uuid:pk>/activation/', AutomationRuleActivationForTMDToggleView.as_view(), name='automation-rule-activation'),
    
    # Legacy Email Template Endpoints
    path('email/templates/', EmailTemplateListCreateView.as_view(), name='email-template-list-create'),
    path('email/templates/<uuid:pk>/', EmailTemplateDetailView.as_view(), name='email-template-detail'),
    path('email/templates/<uuid:pk>/activation/', EmailTemplateActivationForTMDToggleView.as_view(), name='email-template-activation'),
]
