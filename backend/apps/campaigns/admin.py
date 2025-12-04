"""
Django Admin configuration for Campaigns application.
Simplified to avoid field validation errors.
"""

from django.contrib import admin
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
    list_display = ['template_name', 'category', 'is_active', 'is_published']
    list_filter = ['category', 'is_active', 'is_published']
    search_fields = ['template_name', 'email_subject']


@admin.register(SMSConfigurationModel)
class SMSConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name_or_type', 'is_active']
    list_filter = ['is_active']


@admin.register(SMSTemplate)
class SMSTemplateAdmin(admin.ModelAdmin):
    list_display = ['template_name', 'is_active', 'is_published']
    list_filter = ['is_active', 'is_published']


@admin.register(OrganizationEmailConfiguration)
class OrganizationEmailConfigurationAdmin(admin.ModelAdmin):
    list_display = ['plan_type', 'is_active', 'is_suspended']
    list_filter = ['plan_type', 'is_active', 'is_suspended']
    search_fields = ['organization__name']


@admin.register(EmailProvider)
class EmailProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider_type', 'is_shared', 'is_active', 'health_status']
    list_filter = ['provider_type', 'is_active', 'is_shared', 'health_status']
    search_fields = ['name']


@admin.register(OrganizationEmailProvider)
class OrganizationEmailProviderAdmin(admin.ModelAdmin):
    list_display = ['provider', 'is_enabled', 'is_primary']
    list_filter = ['is_enabled', 'is_primary']
    search_fields = ['provider__name']


@admin.register(EmailDeliveryLog)
class EmailDeliveryLogAdmin(admin.ModelAdmin):
    list_display = ['recipient_email', 'delivery_status', 'sent_at']
    list_filter = ['delivery_status', 'sent_at']
    search_fields = ['recipient_email']
    date_hierarchy = 'sent_at'


@admin.register(EmailAction)
class EmailActionAdmin(admin.ModelAdmin):
    list_display = ['action_type', 'performed_at']
    list_filter = ['action_type', 'performed_at']


@admin.register(EmailQueue)
class EmailQueueAdmin(admin.ModelAdmin):
    list_display = ['recipient_email', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority']
    search_fields = ['recipient_email']


@admin.register(EmailValidation)
class EmailValidationAdmin(admin.ModelAdmin):
    list_display = ['email_address', 'validation_status', 'is_valid_format']
    list_filter = ['validation_status', 'is_valid_format']
    search_fields = ['email_address']


@admin.register(AutomationRule)
class AutomationRuleAdmin(admin.ModelAdmin):
    list_display = ['automation_name', 'communication_type', 'trigger_type', 'is_active', 'is_published']
    list_filter = ['communication_type', 'trigger_type', 'is_active', 'is_published']
    search_fields = ['automation_name']


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'scheduled_at', 'created_at']
    list_filter = ['status', 'created_at', 'scheduled_at']
    search_fields = ['name']


@admin.register(ContactList)
class ContactListAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'created_at']
    list_filter = ['created_at']
    search_fields = ['email', 'first_name', 'last_name']
