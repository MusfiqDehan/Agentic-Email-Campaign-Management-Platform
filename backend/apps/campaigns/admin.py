"""
Django Admin configuration for Campaigns application.
Simplified to match new model structure.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    EmailTemplate, AutomationRule, SMSConfigurationModel, SMSTemplate,
    OrganizationEmailConfiguration, EmailProvider, OrganizationEmailProvider,
    EmailValidation, EmailQueue, EmailDeliveryLog, EmailAction,
    Campaign, ContactList, Contact,
)
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Basic Admin Registrations
# ============================================================================

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['template_name', 'organization', 'category', 'is_active', 'is_published', 'updated_at']
    list_filter = ['category', 'is_active', 'is_published']
    search_fields = ['template_name', 'email_subject']


@admin.register(SMSConfigurationModel)
class SMSConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name_or_type', 'organization', 'is_active', 'whatsapp_enabled']
    list_filter = ['is_active', 'whatsapp_enabled']


@admin.register(SMSTemplate)
class SMSTemplateAdmin(admin.ModelAdmin):
    list_display = ['template_name', 'organization', 'is_active', 'is_published']
    list_filter = ['is_active', 'is_published']


# ============================================================================
# Organization Email Configuration Admin
# ============================================================================

@admin.register(OrganizationEmailConfiguration)
class OrganizationEmailConfigurationAdmin(admin.ModelAdmin):
    """Enhanced admin for organization email configurations"""
    
    list_display = [
        'organization', 'plan_type', 'is_active', 'is_suspended',
        'emails_sent_today', 'emails_per_day', 'get_usage_percentage', 'reputation_score'
    ]
    list_filter = ['plan_type', 'is_active', 'is_suspended', 'custom_domain_verified']
    search_fields = ['organization__name']
    readonly_fields = [
        'emails_sent_today', 'emails_sent_this_month', 'last_email_sent_at',
        'bounce_rate', 'complaint_rate', 'reputation_score'
    ]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('organization', 'plan_type', 'timezone', 'is_active', 'is_suspended', 'suspension_reason')
        }),
        ('Email Limits', {
            'fields': ('emails_per_day', 'emails_per_month', 'emails_per_minute', 'plan_limits')
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
    
    def get_usage_percentage(self, obj):
        if obj.emails_per_day == 0:
            return mark_safe('<span style="color: orange;">N/A (0 limit)</span>')
        
        percentage = float(obj.emails_sent_today) / float(obj.emails_per_day) * 100.0
        color = 'green' if percentage < 50 else 'orange' if percentage < 80 else 'red'
        percentage_str = f'{percentage:.1f}'
        return format_html(
            '<span style="color: {};">{}%</span>',
            color,
            percentage_str
        )
    get_usage_percentage.short_description = 'Daily Usage %'


# ============================================================================
# Email Provider Admin
# ============================================================================

@admin.register(EmailProvider)
class EmailProviderAdmin(admin.ModelAdmin):
    """Enhanced admin for email providers"""
    
    list_display = [
        'name', 'provider_type', 'is_shared', 'organization',
        'is_active', 'is_default', 'priority', 'health_status'
    ]
    list_filter = ['provider_type', 'is_active', 'is_shared', 'is_default', 'health_status']
    search_fields = ['name']
    readonly_fields = [
        'health_status', 'health_details', 'last_health_check',
        'emails_sent_today', 'emails_sent_this_hour', 'last_used_at'
    ]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'provider_type', 'organization', 'is_shared', 'is_active', 'is_default', 'priority')
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


@admin.register(OrganizationEmailProvider)
class OrganizationEmailProviderAdmin(admin.ModelAdmin):
    """Admin for organization-specific email provider configurations"""
    
    list_display = [
        'organization', 'provider', 'is_enabled', 'is_primary',
        'emails_sent_today', 'delivery_rate', 'bounce_rate'
    ]
    list_filter = ['is_enabled', 'is_primary', 'provider__provider_type']
    search_fields = ['organization__name', 'provider__name']


# ============================================================================
# Email Delivery Admin
# ============================================================================

@admin.register(EmailDeliveryLog)
class EmailDeliveryLogAdmin(admin.ModelAdmin):
    """Enhanced admin for email delivery logs"""
    
    list_display = [
        'recipient_email', 'subject', 'delivery_status', 'get_provider_name',
        'sent_at', 'organization', 'campaign', 'open_count', 'click_count'
    ]
    list_filter = [
        'delivery_status', 'sent_at', 'is_spam', 'is_duplicate',
        ('email_provider', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = ['recipient_email', 'subject', 'sender_email']
    readonly_fields = [
        'sent_at', 'delivered_at', 'opened_at', 'clicked_at', 'bounced_at',
        'provider_message_id'
    ]
    date_hierarchy = 'sent_at'
    
    def get_provider_name(self, obj):
        return obj.email_provider.name if obj.email_provider else 'N/A'
    get_provider_name.short_description = 'Provider'


@admin.register(EmailAction)
class EmailActionAdmin(admin.ModelAdmin):
    """Admin for email actions (resend, forward, etc.)"""
    
    list_display = [
        'action_type', 'get_original_recipient', 'new_recipient', 'performed_at'
    ]
    list_filter = ['action_type', 'performed_at']
    search_fields = ['original_log__recipient_email', 'new_recipient']
    readonly_fields = ['performed_at']
    
    def get_original_recipient(self, obj):
        return obj.original_log.recipient_email
    get_original_recipient.short_description = 'Original Recipient'


@admin.register(EmailQueue)
class EmailQueueAdmin(admin.ModelAdmin):
    """Admin for email queue management"""
    
    list_display = [
        'recipient_email', 'subject', 'status', 'priority',
        'scheduled_at', 'retry_count', 'organization'
    ]
    list_filter = ['status', 'priority', 'scheduled_at']
    search_fields = ['recipient_email', 'subject']
    readonly_fields = ['processed_at', 'retry_count']


@admin.register(EmailValidation)
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


# ============================================================================
# Automation Rule Admin
# ============================================================================

@admin.register(AutomationRule)
class AutomationRuleAdmin(admin.ModelAdmin):
    """Enhanced admin for automation rules"""
    
    list_display = [
        'automation_name', 'organization', 'reason_name',
        'communication_type', 'trigger_type', 'is_active', 'is_published'
    ]
    list_filter = [
        'reason_name', 'communication_type', 'trigger_type',
        'is_active', 'is_published', 'created_at'
    ]
    search_fields = ['automation_name', 'reason_name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('automation_name', 'organization', 'is_active', 'is_published')
        }),
        ('Rule Configuration', {
            'fields': ('reason_name', 'communication_type', 'trigger_type', 'short_description')
        }),
        ('Templates', {
            'fields': ('email_template_id', 'sms_template_id', 'sms_config_id')
        }),
        ('Campaign Integration', {
            'fields': ('campaign', 'contact_list')
        }),
        ('Trigger Configuration', {
            'fields': (
                'delay_amount', 'delay_unit', 'schedule_frequency',
                'schedule_interval_amount', 'schedule_interval_unit',
                'schedule_time', 'schedule_day_of_week', 'schedule_day_of_month'
            ),
            'classes': ('collapse',)
        })
    )


# ============================================================================
# Campaign Management Admin
# ============================================================================

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    """Admin for campaigns"""
    
    list_display = [
        'name', 'organization', 'status', 'scheduled_at',
        'total_recipients', 'sent_count', 'opened_count', 'clicked_count'
    ]
    list_filter = ['status', 'created_at', 'scheduled_at']
    search_fields = ['name', 'organization__name']
    readonly_fields = [
        'total_recipients', 'sent_count', 'delivered_count',
        'opened_count', 'clicked_count', 'bounced_count', 'unsubscribed_count'
    ]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'organization', 'status', 'email_template', 'contact_list')
        }),
        ('Scheduling', {
            'fields': ('scheduled_at', 'started_at', 'completed_at')
        }),
        ('Statistics', {
            'fields': (
                'total_recipients', 'sent_count', 'delivered_count',
                'opened_count', 'clicked_count', 'bounced_count', 'unsubscribed_count'
            ),
            'classes': ('collapse',)
        })
    )


@admin.register(ContactList)
class ContactListAdmin(admin.ModelAdmin):
    """Admin for contact lists"""
    
    list_display = ['name', 'organization', 'contact_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'organization__name']
    readonly_fields = ['contact_count']


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Admin for contacts"""
    
    list_display = [
        'email', 'first_name', 'last_name', 'contact_list',
        'is_subscribed', 'is_bounced', 'created_at'
    ]
    list_filter = ['is_subscribed', 'is_bounced', 'gdpr_consent', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    readonly_fields = ['unsubscribe_token']
