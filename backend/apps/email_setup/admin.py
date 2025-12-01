from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    EmailTemplate, AutomationRule, SMSConfigurationModel, SMSTemplate,
    TenantEmailConfiguration, EmailProvider, TenantEmailProvider, EmailValidation,
    EmailQueue, EmailDeliveryLog, EmailAction, EmailProviderServiceDefinition,
    TenantServiceDefinition
)
from .utils.tenant_service import TenantServiceAPI
import logging

logger = logging.getLogger(__name__)


# Keep existing basic admin registrations
admin.site.register(EmailTemplate)
admin.site.register(SMSConfigurationModel)
admin.site.register(SMSTemplate)


class TenantEmailConfigurationAdmin(admin.ModelAdmin):
    """Enhanced admin for tenant email configurations"""
    
    list_display = [
        'tenant_id', 'get_tenant_name', 'plan_type', 'activated_by_root', 'activated_by_tmd', 'is_suspended',
        'emails_sent_today', 'emails_per_day', 'get_usage_percentage', 'reputation_score'
    ]
    list_filter = ['plan_type', 'activated_by_root', 'activated_by_tmd', 'is_suspended', 'custom_domain_verified']
    search_fields = ['tenant_id']
    readonly_fields = [
        'emails_sent_today', 'emails_sent_this_month', 'last_email_sent_at',
        'bounce_rate', 'complaint_rate', 'reputation_score', 'get_tenant_details'
    ]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('tenant_id', 'get_tenant_details', 'plan_type', 'activated_by_root', 'activated_by_tmd', 'is_suspended', 'suspension_reason')
        }),
        ('Email Limits', {
            'fields': ('emails_per_day', 'emails_per_month', 'emails_per_minute')
        }),
        ('Features', {
            'fields': ('custom_domain_allowed', 'advanced_analytics', 'priority_support', 'bulk_email_allowed')
        }),
        ('Domain Configuration', {
            'fields': ('default_from_domain', 'custom_domain', 'custom_domain_verified')
        }),
        ('Usage Statistics', {
            'fields': ('emails_sent_today', 'emails_sent_this_month', 'last_email_sent_at'),
            'classes': ('collapse',)
        }),
        ('Reputation', {
            'fields': ('bounce_rate', 'complaint_rate', 'reputation_score'),
            'classes': ('collapse',)
        })
    )
    
    def get_tenant_name(self, obj):
        try:
            tenant_info = TenantServiceAPI.get_tenant_details(str(obj.tenant_id))
            return tenant_info.get('name', 'Unknown')
        except Exception:
            return 'Unknown'
    get_tenant_name.short_description = 'Tenant Name'
    
    def get_usage_percentage(self, obj):
        if obj.emails_per_day == 0:
            return mark_safe('<span style="color: orange;">N/A (0 limit)</span>')
        
        # Ensure percentage is a plain float, not a SafeString
        percentage = float(obj.emails_sent_today) / float(obj.emails_per_day) * 100.0
        color = 'green' if percentage < 50 else 'orange' if percentage < 80 else 'red'
        
        # Format the percentage first, then pass to format_html
        percentage_str = f'{percentage:.1f}'
        return format_html(
            '<span style="color: {};">{}%</span>',
            color,
            percentage_str
        )
    get_usage_percentage.short_description = 'Daily Usage %'
    
    def get_tenant_details(self, obj):
        try:
            tenant_info = TenantServiceAPI.get_tenant_details(str(obj.tenant_id))
            return format_html(
                '<strong>Name:</strong> {}<br>'
                '<strong>Email:</strong> {}<br>'
                '<strong>Status:</strong> {}<br>'
                '<strong>Domain:</strong> {}',
                tenant_info.get('name', 'N/A'),
                tenant_info.get('email', 'N/A'),
                tenant_info.get('status', 'N/A'),
                tenant_info.get('domain', 'N/A')
            )
        except Exception as e:
            return f'Error loading tenant details: {e}'
    get_tenant_details.short_description = 'Tenant Details'


class EmailProviderAdmin(admin.ModelAdmin):
    """Enhanced admin for email providers"""
    
    list_display = [
        'name', 'provider_type', 'get_scope', 'activated_by_root', 'activated_by_tmd', 'is_default', 'priority',
        'health_status', 'get_config_status', 'emails_sent_today', 'last_used_at'
    ]
    list_filter = ['provider_type', 'activated_by_root', 'activated_by_tmd', 'is_default', 'health_status', 'is_global']
    search_fields = ['name', 'tenant_id']
    readonly_fields = [
        'health_status', 'health_details', 'last_health_check',
        'emails_sent_today', 'emails_sent_this_hour', 'last_used_at', 'tenant_id', 'is_global'
    ]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'provider_type', 'tenant_id', 'is_global', 'activated_by_root', 'activated_by_tmd', 'is_default', 'priority')
        }),
        ('Rate Limits', {
            'fields': ('max_emails_per_minute', 'max_emails_per_hour', 'max_emails_per_day')
        }),
        ('Health Status', {
            'fields': ('health_status', 'health_details', 'last_health_check'),
            'classes': ('collapse',)
        }),
        ('Usage Statistics', {
            'fields': ('emails_sent_today', 'emails_sent_this_hour', 'last_used_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_scope(self, obj):
        """Display whether provider is global or tenant-specific"""
        if obj.tenant_id and not obj.is_global:
            return format_html(
                '<span style="color: blue; background-color: #e3f2fd; padding: 2px 6px; border-radius: 3px;">'
                'Tenant: {}</span>',
                str(obj.tenant_id)[:8] + '...'
            )
        elif obj.is_global:
            return format_html(
                '<span style="color: green; background-color: #e8f5e9; padding: 2px 6px; border-radius: 3px;">'
                'Global</span>'
            )
        return '-'
    get_scope.short_description = 'Scope'
    
    def get_config_status(self, obj):
        try:
            from .utils.email_providers import EmailProviderFactory
            config = obj.decrypt_config()
            provider = EmailProviderFactory.create_provider(obj.provider_type, config)
            is_valid, message = provider.validate_config(config)
            
            color = 'green' if is_valid else 'red'
            return format_html(
                '<span style="color: {};">{}</span>',
                color, 'Valid' if is_valid else 'Invalid'
            )
        except Exception as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e))
    get_config_status.short_description = 'Config Status'


class TenantEmailProviderAdmin(admin.ModelAdmin):
    """Admin for tenant-specific email provider configurations"""
    
    list_display = [
        'tenant_id', 'get_provider_name', 'is_enabled', 'is_primary',
        'emails_sent_today', 'delivery_rate', 'bounce_rate'
    ]
    list_filter = ['is_enabled', 'is_primary', 'provider__provider_type']
    search_fields = ['tenant_id', 'provider__name']
    
    def get_provider_name(self, obj):
        return f"{obj.provider.name} ({obj.provider.provider_type})"
    get_provider_name.short_description = 'Provider'


class EmailDeliveryLogAdmin(admin.ModelAdmin):
    """Enhanced admin for email delivery logs"""
    
    list_display = [
        'recipient_email', 'subject', 'delivery_status', 'get_provider_name',
        'sent_at', 'get_tenant_name', 'open_count', 'click_count'
    ]
    list_filter = [
        'delivery_status', 'sent_at', 'is_spam', 'is_duplicate',
        ('email_provider', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = ['recipient_email', 'subject', 'sender_email', 'tenant_id']
    readonly_fields = [
        'sent_at', 'delivered_at', 'opened_at', 'clicked_at', 'bounced_at',
        'provider_message_id', 'get_automation_rule_link'
    ]
    date_hierarchy = 'sent_at'
    
    fieldsets = (
        ('Email Details', {
            'fields': ('recipient_email', 'sender_email', 'subject', 'delivery_status')
        }),
        ('Tracking', {
            'fields': ('automation_rule', 'get_automation_rule_link', 'tenant_id', 'email_provider', 'provider_message_id')
        }),
        ('Timestamps', {
            'fields': ('sent_at', 'delivered_at', 'opened_at', 'clicked_at', 'bounced_at'),
            'classes': ('collapse',)
        }),
        ('Engagement', {
            'fields': ('open_count', 'click_count', 'unique_click_count'),
            'classes': ('collapse',)
        }),
        ('Error Details', {
            'fields': ('bounce_type', 'bounce_reason', 'spam_score', 'is_spam'),
            'classes': ('collapse',)
        }),
        ('Duplicate Detection', {
            'fields': ('is_duplicate', 'duplicate_of'),
            'classes': ('collapse',)
        })
    )
    
    def get_provider_name(self, obj):
        return obj.email_provider.name if obj.email_provider else 'N/A'
    get_provider_name.short_description = 'Provider'
    
    def get_tenant_name(self, obj):
        try:
            tenant_info = TenantServiceAPI.get_tenant_details(str(obj.tenant_id))
            return tenant_info.get('name', 'Unknown')
        except Exception:
            return 'Unknown'
    get_tenant_name.short_description = 'Tenant'
    
    def get_automation_rule_link(self, obj):
        if obj.automation_rule:
            url = reverse('admin:automation_rule_automationrule_change', args=[obj.automation_rule.id])
            return format_html('<a href="{}">{}</a>', url, obj.automation_rule.automation_name)
        return 'N/A'
    get_automation_rule_link.short_description = 'Automation Rule'


class EmailActionAdmin(admin.ModelAdmin):
    """Admin for email actions (resend, forward, etc.)"""
    
    list_display = [
        'action_type', 'get_original_recipient', 'new_recipient',
        'performed_at', 'get_performed_by_name'
    ]
    list_filter = ['action_type', 'performed_at']
    search_fields = ['original_log__recipient_email', 'new_recipient']
    readonly_fields = ['performed_at']
    
    def get_original_recipient(self, obj):
        return obj.original_log.recipient_email
    get_original_recipient.short_description = 'Original Recipient'
    
    def get_performed_by_name(self, obj):
        if not obj.performed_by:
            return 'System'
        
        try:
            from core.utils.auth_service import AuthServiceAPI
            user_info = AuthServiceAPI.get_user_details(str(obj.performed_by))
            return user_info.get('full_name', 'Unknown User')
        except Exception:
            return 'Unknown User'
    get_performed_by_name.short_description = 'Performed By'


class EmailQueueAdmin(admin.ModelAdmin):
    """Admin for email queue management"""
    
    list_display = [
        'recipient_email', 'subject', 'status', 'priority',
        'scheduled_at', 'retry_count', 'get_tenant_name'
    ]
    list_filter = ['status', 'priority', 'scheduled_at']
    search_fields = ['recipient_email', 'subject', 'tenant_id']
    readonly_fields = ['processed_at', 'retry_count']
    
    def get_tenant_name(self, obj):
        try:
            tenant_info = TenantServiceAPI.get_tenant_details(str(obj.tenant_id))
            return tenant_info.get('name', 'Unknown')
        except Exception:
            return 'Unknown'
    get_tenant_name.short_description = 'Tenant'


class EmailValidationAdmin(admin.ModelAdmin):
    """Admin for email validation records"""
    
    list_display = [
        'email_address', 'validation_status', 'validation_score',
        'bounce_count', 'successful_deliveries', 'is_blacklisted'
    ]
    list_filter = [
        'validation_status', 'is_valid_format', 'is_disposable',
        'is_role_based', 'is_blacklisted'
    ]
    search_fields = ['email_address']
    readonly_fields = ['last_validated_at', 'validation_score']


class EnhancedAutomationRuleAdmin(admin.ModelAdmin):
    """Enhanced admin for automation rules"""
    
    list_display = [
        'automation_name', 'get_tenant_name', 'reason_name',
        'communication_type', 'trigger_type', 'get_provider_info', 
        'activated_by_root', 'activated_by_tmd', 'priority'
    ]
    list_filter = [
        'reason_name', 'communication_type', 'trigger_type',
        'activated_by_root', 'activated_by_tmd', 'created_at'
    ]
    search_fields = ['automation_name', 'tenant_id', 'reason_name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('automation_name', 'tenant_id', 'product_id', 'activated_by_root', 'activated_by_tmd', 'priority')
        }),
        ('Rule Configuration', {
            'fields': ('reason_name', 'communication_type', 'trigger_type', 'action_name', 'short_description')
        }),
        ('Templates & Configuration', {
            'fields': (
                'email_template_id', 
                'sms_template_id', 
                'tenant_email_config', 
                'preferred_email_provider',
                'preferred_global_provider'
            ),
            'description': 'For tenant rules, use preferred_email_provider. For global rules, use preferred_global_provider.'
        }),
        ('Trigger Configuration', {
            'fields': (
                'delay_amount', 'delay_unit', 'schedule_frequency',
                'schedule_interval_amount', 'schedule_interval_unit',
                'schedule_time', 'schedule_day_of_week', 'schedule_day_of_month'
            ),
            'classes': ('collapse',)
        }),
        ('Advanced Settings', {
            'fields': ('max_retries', 'retry_delay_minutes', 'batch_size', 'filter_conditions'),
            'classes': ('collapse',)
        })
    )
    
    def get_tenant_name(self, obj):
        try:
            tenant_info = TenantServiceAPI.get_tenant_details(str(obj.tenant_id))
            return tenant_info.get('name', 'Unknown')
        except Exception:
            return 'Unknown'
    get_tenant_name.short_description = 'Tenant'
    
    def get_provider_info(self, obj):
        """Show which provider is configured for this rule"""
        if obj.preferred_email_provider:
            return format_html(
                '<span style="color: blue;" title="Tenant-specific provider">🔹 {}</span>',
                obj.preferred_email_provider.provider.name
            )
        elif obj.preferred_global_provider:
            return format_html(
                '<span style="color: green;" title="Global provider">🌐 {}</span>',
                obj.preferred_global_provider.name
            )
        else:
            return format_html('<span style="color: gray;">Default</span>')
    get_provider_info.short_description = 'Provider'


# Register enhanced admin classes
admin.site.register(TenantEmailConfiguration, TenantEmailConfigurationAdmin)
admin.site.register(EmailProvider, EmailProviderAdmin)
admin.site.register(TenantEmailProvider, TenantEmailProviderAdmin)
admin.site.register(EmailDeliveryLog, EmailDeliveryLogAdmin)
admin.site.register(EmailAction, EmailActionAdmin)
admin.site.register(EmailQueue, EmailQueueAdmin)
admin.site.register(EmailValidation, EmailValidationAdmin)

class EmailProviderServiceDefinitionAdmin(admin.ModelAdmin):
    """Admin for email provider service definition bridge"""
    
    list_display = [
        'get_provider_name', 'get_service_name', 'sync_status',
        'last_sync_at', 'get_active_status'
    ]
    list_filter = ['sync_status', 'service_integration__service_type']
    search_fields = ['email_provider__name', 'service_integration__service_name']
    readonly_fields = ['last_sync_at', 'sync_error_message']
    
    fieldsets = (
        ('Integration', {
            'fields': ('service_integration', 'email_provider')
        }),
        ('Sync Status', {
            'fields': ('sync_status', 'last_sync_at', 'sync_error_message')
        }),
        ('Configuration', {
            'fields': ('webhook_url', 'callback_secret'),
            'classes': ('collapse',)
        })
    )
    
    def get_provider_name(self, obj):
        return f"{obj.email_provider.name} ({obj.email_provider.provider_type})"
    get_provider_name.short_description = 'Email Provider'
    
    def get_service_name(self, obj):
        return obj.service_integration.service_name
    get_service_name.short_description = 'Service Integration'
    
    def get_active_status(self, obj):
        # Since EmailProviderServiceDefinition inherits from BaseModel, it should have activated_by_root
        if hasattr(obj, 'activated_by_root'):
            return obj.activated_by_root
        return "Unknown"
    get_active_status.short_description = 'Active Status'
    
    actions = ['sync_configurations']
    
    def sync_configurations(self, request, queryset):
        synced = 0
        errors = 0
        for integration in queryset:
            if integration.sync_configuration():
                synced += 1
            else:
                errors += 1
        
        message = f"Synced {synced} integrations"
        if errors > 0:
            message += f", {errors} errors"
        
        self.message_user(request, message)
    sync_configurations.short_description = "Sync selected configurations"


class TenantServiceDefinitionAdmin(admin.ModelAdmin):
    """Admin for tenant service definitions"""

    list_display = [
        'get_account_name', 'get_provider_name', 'is_verified',
        'usage_count', 'last_used_at', 'get_active_status'
    ]
    list_filter = ['is_verified', 'created_at']
    search_fields = [
        'service_integration__account_name',
        'service_integration__service_name',
        'service_integration__account_identifier'
    ]
    readonly_fields = ['last_used_at', 'usage_count', 'verified_at', 'created_at', 'updated_at']
    
    def get_account_name(self, obj):
        return obj.service_integration.account_name if obj.service_integration else "No Account"
    get_account_name.short_description = 'Account Name'
    
    def get_provider_name(self, obj):
        return str(obj.tenant_email_provider) if obj.tenant_email_provider else "No Provider"
    get_provider_name.short_description = 'Email Provider'
    
    def get_active_status(self, obj):
        # Since TenantServiceIntegration inherits from BaseModel, it should have activated_by_root
        if hasattr(obj, 'activated_by_root'):
            return obj.activated_by_root
        return "Unknown"
    get_active_status.short_description = 'Active Status'


# Register additional enhanced admin classes
admin.site.register(EmailProviderServiceDefinition, EmailProviderServiceDefinitionAdmin)
admin.site.register(TenantServiceDefinition, TenantServiceDefinitionAdmin)

# Unregister and re-register AutomationRule with enhanced admin
try:
    admin.site.unregister(AutomationRule)
except admin.sites.NotRegistered:
    pass  # AutomationRule was not registered, so no need to unregister
admin.site.register(AutomationRule, EnhancedAutomationRuleAdmin)
