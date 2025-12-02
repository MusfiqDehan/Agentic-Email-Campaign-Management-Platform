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
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import campaign views
from .views import (
    # Campaign ViewSets (new)
    ContactListViewSet,
    ContactViewSet,
    CampaignViewSet,
    
    # Admin ViewSets (new)
    AdminEmailProviderViewSet,
    AdminOrganizationConfigViewSet,
    
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
)

# Import enhanced views
from .views.enhanced_views import (
    # Organization Email Configuration Views
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
    
    # Organization Email Provider Views
    TenantEmailProviderListCreateView,
    TenantEmailProviderDetailView,
    
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

# Setup routers for ViewSets
router = DefaultRouter()
router.register(r'contact-lists', ContactListViewSet, basename='contact-list')
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'campaigns', CampaignViewSet, basename='campaign')

# Admin router
admin_router = DefaultRouter()
admin_router.register(r'providers', AdminEmailProviderViewSet, basename='admin-provider')
admin_router.register(r'organizations', AdminOrganizationConfigViewSet, basename='admin-org')


urlpatterns = [
    # ========================================================================
    # SECTION 1: CAMPAIGN MANAGEMENT (New REST ViewSets)
    # ========================================================================
    
    # Include router URLs (campaigns, contacts, contact lists)
    path('', include(router.urls)),
    
    # ========================================================================
    # SECTION 2: EMAIL CONFIGURATION
    # Organization-scoped email settings
    # ========================================================================
    
    # Email Templates
    path('templates/', EmailTemplateListCreateView.as_view(), name='email-template-list-create'),
    path('templates/<uuid:pk>/', EmailTemplateDetailView.as_view(), name='email-template-detail'),
    
    # Organization Email Configuration
    path('config/', TenantEmailConfigurationListCreateView.as_view(), name='org-email-config-list'),
    path('config/<uuid:pk>/', TenantEmailConfigurationDetailView.as_view(), name='org-email-config-detail'),
    path('config/<uuid:pk>/reset-usage/', TenantEmailConfigurationResetUsageView.as_view(), name='org-email-config-reset-usage'),
    path('config/<uuid:pk>/verify-domain/', TenantEmailConfigurationVerifyDomainView.as_view(), name='org-email-config-verify-domain'),
    path('config/usage-stats/', TenantEmailConfigurationUsageStatsView.as_view(), name='org-email-config-usage-stats'),
    
    # Organization Email Providers
    path('providers/', TenantEmailProviderListCreateView.as_view(), name='org-email-provider-list-create'),
    path('providers/<uuid:pk>/', TenantEmailProviderDetailView.as_view(), name='org-email-provider-detail'),
    
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
    
    path('admin/', include(admin_router.urls)),
    
    # ========================================================================
    # SECTION 7: MONITORING & DEBUGGING
    # ========================================================================
    
    path('stats/', AutomationStatsView.as_view(), name='automation-stats'),
    path('dispatches/', EmailDispatchReportView.as_view(), name='email-dispatch-report'),
    path('health/', DebugAutoHealthCheckView.as_view(), name='health-check'),
]
