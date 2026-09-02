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
from django_ses.views import SESEventWebhookView
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
    ContactToggleStatusView,
    
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
    OrganizationStatsView,
    
    # Public Views
    GDPRForgetView,
    PublicContactSubscribeView,
    
    # Admin Views
    AdminEmailProviderListCreateView,
    AdminEmailProviderDetailView,
    AdminEmailProviderSetDefaultView,
    AdminEmailProviderHealthCheckView,
    AdminEmailProviderTestSendView,
    AdminOrganizationConfigListView,
    AdminOrganizationConfigDetailView,
    AdminOrganizationActivateView,
    AdminOrganizationDeactivateView,
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

    GenerateEmailContentAIView,
    ContactAgentView
)

# Import notification views
from .views.notification_views import (
    NotificationListView,
    UnreadNotificationCountView,
    MarkNotificationReadView,
    MarkAllNotificationsReadView,
    DeleteNotificationView,
)

# Import push notification views
from .views.push_views import PushSubscriptionViewSet

# Import tracking + mailbox views
from .views.tracking_views import TrackOpenView, TrackClickView
from .views.domain_views import (
    SendingDomainListCreateView,
    SendingDomainDetailView,
    SendingDomainDNSRecordsView,
    SendingDomainVerifyNowView,
    SenderEmailListCreateView,
    SenderEmailDetailView,
)
from .views.admin_package_views import (
    AdminPackageListCreateView,
    AdminPackageDetailView,
    AdminOrganizationAssignPackageView,
    AdminOrganizationLimitOverridesView,
    AdminOrganizationDomainFeatureView,
    AdminOrganizationDomainUsageView,
    AdminOrganizationDomainCreateView,
    AdminOrganizationSenderEmailCreateView,
    AdminSendingDomainListView,
    AdminSendingDomainSuspendView,
    AdminSendingDomainReactivateView,
    AdminSenderEmailSuspendView,
    AdminSenderEmailReactivateView,
)
from .views.package_views import (
    PackageCatalogView,
    PackageUpgradeView,
)
from .views.mailbox_views import (
    EmailAccountListCreateView,
    EmailAccountDetailView,
    EmailAccountSyncView,
    MailboxMessageListView,
    MailboxMessageDetailView,
    MailboxComposeView,
    MailboxStatsView,
)
from .views.provider_webhooks import (
    SendGridEventWebhookView,
    BrevoEventWebhookView,
    SendGridInboundParseView,
)
from .views.unsubscribe_views import UnsubscribeView

# Import template operation views
from .views.template_operations import (
    EmailTemplateUseView,
    EmailTemplateBulkUseView,
    EmailTemplateDuplicateView,
    EmailTemplateVersionHistoryView,
    EmailTemplateCreateVersionView,
    EmailTemplateSubmitForApprovalView,
    TemplateApprovalReviewView,
    TemplatePreviewTestView,
    EmailTemplateUpdateFromGlobalView,
)

# Import admin template views
from .views.admin_templates import (
    AdminGlobalTemplateListCreateView,
    AdminGlobalTemplateDetailView,
    AdminTemplateAnalyticsView,
    AdminTemplateAnalyticsSummaryView,
    AdminPendingApprovalsView,
)

# Import organization admin views
from .views.organization_admin import (
    OrganizationTemplateUsageView,
    OrganizationTemplateNotificationsView,
    OrganizationTemplateNotificationMarkReadView,
    OrganizationTemplateUpdateStatusView,
    OrganizationTeamTemplateStatsView,
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
    path('contacts/<uuid:pk>/toggle-status/', ContactToggleStatusView.as_view(), name='contact-toggle-status'),
    
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

    # Self-service package catalog / upgrade (sidebar "Upgrade to Pro")
    path('packages/catalog/', PackageCatalogView.as_view(), name='package-catalog'),
    path('packages/upgrade/', PackageUpgradeView.as_view(), name='package-upgrade'),
    
    # Organization Email Providers (links org to shared/platform providers)
    path('providers/', OrganizationEmailProviderListCreateView.as_view(), name='org-email-provider-list-create'),
    path('providers/<uuid:pk>/', OrganizationEmailProviderDetailView.as_view(), name='org-email-provider-detail'),

    # Organization Own Email Providers (org-owned providers created by org admins)
    path('org/providers/', OrganizationOwnEmailProviderListCreateView.as_view(), name='org-own-provider-list-create'),
    path('org/providers/<uuid:pk>/', OrganizationOwnEmailProviderDetailView.as_view(), name='org-own-provider-detail'),
    path('org/providers/<uuid:pk>/health-check/', OrganizationOwnEmailProviderHealthCheckView.as_view(), name='org-own-provider-health-check'),
    path('org/providers/<uuid:pk>/test-send/', OrganizationOwnEmailProviderTestSendView.as_view(), name='org-own-provider-test-send'),
    
    # Shared Email Providers (read-only for regular users)
    path('shared-providers/', EmailProviderListCreateView.as_view(), name='shared-email-provider-list'),
    path('shared-providers/<uuid:pk>/', EmailProviderDetailView.as_view(), name='shared-email-provider-detail'),
    path('shared-providers/<uuid:pk>/health-check/', EmailProviderHealthCheckView.as_view(), name='shared-email-provider-health-check'),

    # Sending Domains (AWS SES identities) + dynamic sender emails
    path('domains/', SendingDomainListCreateView.as_view(), name='sending-domain-list-create'),
    path('domains/<uuid:pk>/', SendingDomainDetailView.as_view(), name='sending-domain-detail'),
    path('domains/<uuid:pk>/dns-records/', SendingDomainDNSRecordsView.as_view(), name='sending-domain-dns-records'),
    path('domains/<uuid:pk>/verify/', SendingDomainVerifyNowView.as_view(), name='sending-domain-verify'),
    path('sender-emails/', SenderEmailListCreateView.as_view(), name='sender-email-list-create'),
    path('sender-emails/<uuid:pk>/', SenderEmailDetailView.as_view(), name='sender-email-detail'),
    
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

    # First-party open/click tracking (public)
    path('track/open/<path:token>', TrackOpenView.as_view(), name='track-open'),
    path('track/click/<path:token>/', TrackClickView.as_view(), name='track-click'),

    # Mailbox (Gmail-like send + receive)
    path('mailbox/accounts/', EmailAccountListCreateView.as_view(), name='mailbox-account-list'),
    path('mailbox/accounts/<uuid:pk>/', EmailAccountDetailView.as_view(), name='mailbox-account-detail'),
    path('mailbox/accounts/<uuid:pk>/sync/', EmailAccountSyncView.as_view(), name='mailbox-account-sync'),
    path('mailbox/messages/', MailboxMessageListView.as_view(), name='mailbox-message-list'),
    path('mailbox/messages/<uuid:pk>/', MailboxMessageDetailView.as_view(), name='mailbox-message-detail'),
    path('mailbox/compose/', MailboxComposeView.as_view(), name='mailbox-compose'),
    path('mailbox/stats/', MailboxStatsView.as_view(), name='mailbox-stats'),

    # AWS SES SNS webhook (bounce/complaint/delivery/open/click/received)
    path('webhooks/ses/', SESEventWebhookView.as_view(), name='ses-event-webhook'),
    # SendGrid / Brevo event + inbound webhooks
    path('webhooks/sendgrid/', SendGridEventWebhookView.as_view(), name='sendgrid-event-webhook'),
    path('webhooks/sendgrid/inbound/', SendGridInboundParseView.as_view(), name='sendgrid-inbound'),
    path('webhooks/brevo/', BrevoEventWebhookView.as_view(), name='brevo-event-webhook'),
    
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
    path('admin/organizations/<uuid:pk>/activate/', AdminOrganizationActivateView.as_view(), name='admin-org-activate'),
    path('admin/organizations/<uuid:pk>/deactivate/', AdminOrganizationDeactivateView.as_view(), name='admin-org-deactivate'),
    path('admin/organizations/<uuid:pk>/suspend/', AdminOrganizationSuspendView.as_view(), name='admin-org-suspend'),
    path('admin/organizations/<uuid:pk>/unsuspend/', AdminOrganizationUnsuspendView.as_view(), name='admin-org-unsuspend'),
    path('admin/organizations/<uuid:pk>/upgrade-plan/', AdminOrganizationUpgradePlanView.as_view(), name='admin-org-upgrade-plan'),

    # Admin Packages (DB-backed plan catalog)
    path('admin/packages/', AdminPackageListCreateView.as_view(), name='admin-package-list-create'),
    path('admin/packages/<uuid:pk>/', AdminPackageDetailView.as_view(), name='admin-package-detail'),

    # Admin per-organization package / limits / feature control
    path('admin/organizations/<uuid:pk>/assign-package/', AdminOrganizationAssignPackageView.as_view(), name='admin-org-assign-package'),
    path('admin/organizations/<uuid:pk>/limit-overrides/', AdminOrganizationLimitOverridesView.as_view(), name='admin-org-limit-overrides'),
    path('admin/organizations/<uuid:pk>/domain-feature/', AdminOrganizationDomainFeatureView.as_view(), name='admin-org-domain-feature'),
    path('admin/organizations/<uuid:pk>/domain-usage/', AdminOrganizationDomainUsageView.as_view(), name='admin-org-domain-usage'),
    path('admin/organizations/<uuid:pk>/domains/', AdminOrganizationDomainCreateView.as_view(), name='admin-org-domain-create'),
    path('admin/organizations/<uuid:pk>/sender-emails/', AdminOrganizationSenderEmailCreateView.as_view(), name='admin-org-sender-email-create'),

    # Admin cross-tenant domain / sender-email control
    path('admin/domains/', AdminSendingDomainListView.as_view(), name='admin-domain-list'),
    path('admin/domains/<uuid:pk>/suspend/', AdminSendingDomainSuspendView.as_view(), name='admin-domain-suspend'),
    path('admin/domains/<uuid:pk>/reactivate/', AdminSendingDomainReactivateView.as_view(), name='admin-domain-reactivate'),
    path('admin/sender-emails/<uuid:pk>/suspend/', AdminSenderEmailSuspendView.as_view(), name='admin-sender-email-suspend'),
    path('admin/sender-emails/<uuid:pk>/reactivate/', AdminSenderEmailReactivateView.as_view(), name='admin-sender-email-reactivate'),

    # Admin Platform Stats
    path('admin/stats/', AdminPlatformStatsView.as_view(), name='admin-platform-stats'),
    
    # ========================================================================
    # SECTION 7: PUBLIC ENDPOINTS
    # ========================================================================
    
    path('unsubscribe/', UnsubscribeView.as_view(), name='unsubscribe'),
    path('gdpr/forget/', GDPRForgetView.as_view(), name='gdpr-forget'),
    path('public/subscribe/', PublicContactSubscribeView.as_view(), name='public-subscribe'),
    
    # ========================================================================
    # SECTION 8: MONITORING & DEBUGGING
    # ========================================================================
    # Statistics & Analytics
    path('org/stats/', OrganizationStatsView.as_view(), name='org-stats'),
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

    # ========================================================================
    # SECTION 10: AI & AGENT INTEGRATIONS
    # ========================================================================
    path('ai/generate/email/content/', GenerateEmailContentAIView.as_view(), name='generate-email-content-ai'),
    path('ai/agent/contacts/', ContactAgentView.as_view(), name='contact-agent'),
    
    # ========================================================================
    # SECTION 11: TEMPLATE OPERATIONS
    # ========================================================================
    # Template duplication and usage
    path('templates/<uuid:pk>/use/', EmailTemplateUseView.as_view(), name='template-use'),
    path('templates/<uuid:pk>/duplicate/', EmailTemplateDuplicateView.as_view(), name='template-duplicate'),
    path('templates/bulk-use/', EmailTemplateBulkUseView.as_view(), name='template-bulk-use'),
    
    # Template versioning
    path('templates/<uuid:pk>/versions/', EmailTemplateVersionHistoryView.as_view(), name='template-versions'),
    path('templates/<uuid:pk>/create-version/', EmailTemplateCreateVersionView.as_view(), name='template-create-version'),
    
    # Approval workflow
    path('templates/<uuid:pk>/submit-approval/', EmailTemplateSubmitForApprovalView.as_view(), name='template-submit-approval'),
    path('approvals/<uuid:pk>/review/', TemplateApprovalReviewView.as_view(), name='template-approval-review'),
    
    # Preview and testing
    path('templates/preview-test/', TemplatePreviewTestView.as_view(), name='template-preview-test'),
    
    # Template updates
    path('templates/<uuid:pk>/update-from-global/', EmailTemplateUpdateFromGlobalView.as_view(), name='template-update-from-global'),
    
    # ========================================================================
    # SECTION 12: ADMIN TEMPLATE MANAGEMENT
    # ========================================================================
    # Global template management
    path('admin/templates/', AdminGlobalTemplateListCreateView.as_view(), name='admin-templates-list'),
    path('admin/templates/<uuid:pk>/', AdminGlobalTemplateDetailView.as_view(), name='admin-template-detail'),
    
    # Template analytics
    path('admin/templates/<uuid:pk>/analytics/', AdminTemplateAnalyticsView.as_view(), name='admin-template-analytics'),
    path('admin/templates/analytics/summary/', AdminTemplateAnalyticsSummaryView.as_view(), name='admin-template-analytics-summary'),
    
    # Approval management
    path('admin/approvals/pending/', AdminPendingApprovalsView.as_view(), name='admin-pending-approvals'),
    
    # ========================================================================
    # SECTION 13: ORGANIZATION ADMIN INSIGHTS
    # ========================================================================
    # Template usage tracking
    path('organization/template-usage/', OrganizationTemplateUsageView.as_view(), name='organization-template-usage'),
    
    # Template notifications
    path('organization/template-notifications/', OrganizationTemplateNotificationsView.as_view(), name='organization-template-notifications'),
    path('organization/template-notifications/<uuid:pk>/mark-read/', OrganizationTemplateNotificationMarkReadView.as_view(), name='organization-notification-mark-read'),
    
    # Update status and stats
    path('organization/template-updates/', OrganizationTemplateUpdateStatusView.as_view(), name='organization-template-updates'),
    path('organization/team-template-stats/', OrganizationTeamTemplateStatsView.as_view(), name='organization-team-stats'),
    
    # ========================================================================
    # SECTION 14: NOTIFICATIONS
    # Real-time notifications for campaigns and system events
    # ========================================================================
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/unread-count/', UnreadNotificationCountView.as_view(), name='notification-unread-count'),
    path('notifications/<uuid:pk>/mark-read/', MarkNotificationReadView.as_view(), name='notification-mark-read'),
    path('notifications/mark-all-read/', MarkAllNotificationsReadView.as_view(), name='notification-mark-all-read'),
    path('notifications/<uuid:pk>/', DeleteNotificationView.as_view(), name='notification-delete'),
    
    # ========================================================================
    # SECTION 15: PUSH NOTIFICATIONS
    # Browser push notification subscriptions
    # ========================================================================
    path('push/subscribe/', PushSubscriptionViewSet.as_view({'post': 'create'}), name='push-subscribe'),
    path('push/subscriptions/', PushSubscriptionViewSet.as_view({'get': 'list'}), name='push-subscriptions'),
    path('push/unsubscribe/', PushSubscriptionViewSet.as_view({'delete': 'destroy'}), name='push-unsubscribe'),
    path('push/test/', PushSubscriptionViewSet.as_view({'post': 'test'}), name='push-test'),
]
