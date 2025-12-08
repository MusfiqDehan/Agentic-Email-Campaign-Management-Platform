"""
Base Serializers for Campaigns Application

Simplified serializers with organization-based scoping.
Removed deprecated fields: template_type, rule_scope, product_id, activated_by_*
"""

from rest_framework import serializers
from ..models import (
    EmailTemplate, AutomationRule, SMSConfigurationModel, 
    SMSTemplate, OrganizationEmailConfiguration, EmailProvider, EmailDeliveryLog
)
from ..utils import encrypt_data
import logging

logger = logging.getLogger(__name__)


class EmailTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for email templates.
    All templates are organization-scoped.
    """
    organization_id = serializers.UUIDField(write_only=True, required=False)
    category = serializers.ChoiceField(
        choices=EmailTemplate.TemplateCategory.choices,
        required=False,
        default=EmailTemplate.TemplateCategory.OTHER
    )

    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'organization', 'organization_id', 'template_name', 'category', 
            'email_subject', 'preview_text', 'email_body', 'text_body',
            'default_from_name', 'default_from_email', 'default_reply_to',
            'description', 'tags', 'variable_schema',
            'is_active', 'is_published', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'organization', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        # Get organization_id from validated_data or context
        organization_id = validated_data.pop('organization_id', None)
        
        if not organization_id and 'request' in self.context:
            # Try to get from request user
            request = self.context['request']
            if hasattr(request.user, 'organization_id'):
                organization_id = request.user.organization_id
        
        if not organization_id:
            raise serializers.ValidationError({
                'organization_id': 'Organization ID is required. Provide it in the request or authenticate with an organization.'
            })
        
        validated_data['organization_id'] = organization_id
        return super().create(validated_data)


class AutomationRuleSerializer(serializers.ModelSerializer):
    """
    Serializer for automation rules.
    All rules are organization-scoped.
    """
    organization_id = serializers.UUIDField(source='organization.id', read_only=True)
    campaign_id = serializers.UUIDField(source='campaign.id', read_only=True, allow_null=True)
    contact_list_id = serializers.UUIDField(source='contact_list.id', read_only=True, allow_null=True)

    class Meta:
        model = AutomationRule
        fields = [
            'id', 'automation_name', 'organization_id', 'campaign_id', 'contact_list_id',
            'reason_name', 'trigger_type', 'schedule_frequency',
            'communication_type', 'short_description', 'email_template_id', 'sms_template_id',
            'sms_config_id', 'delay_amount', 'delay_unit',
            'schedule_interval_amount', 'schedule_interval_unit', 'schedule_time',
            'schedule_day_of_week', 'schedule_day_of_month', 'is_active', 'is_published',
            'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'organization_id', 'periodic_task', 'created_at', 'updated_at')

    def validate(self, data):
        """
        Add custom validation based on the trigger_type and schedule_frequency.
        """
        trigger_type = data.get('trigger_type')

        if trigger_type == AutomationRule.TriggerType.DELAY:
            if not data.get('delay_amount') or not data.get('delay_unit'):
                raise serializers.ValidationError(
                    "For a 'DELAY' trigger, 'delay_amount' and 'delay_unit' are required."
                )

        elif trigger_type == AutomationRule.TriggerType.SCHEDULE:
            frequency = data.get('schedule_frequency')
            if not frequency:
                raise serializers.ValidationError(
                    "For a 'SCHEDULE' trigger, 'schedule_frequency' is required."
                )
            
            if frequency == AutomationRule.ScheduleFrequency.INTERVAL:
                if not data.get('schedule_interval_amount') or not data.get('schedule_interval_unit'):
                    raise serializers.ValidationError(
                        "For 'INTERVAL' frequency, 'schedule_interval_amount' and "
                        "'schedule_interval_unit' are required."
                    )
            else:  # DAILY, WEEKLY, MONTHLY
                if not data.get('schedule_time'):
                    raise serializers.ValidationError(
                        "For 'DAILY', 'WEEKLY', or 'MONTHLY' frequency, 'schedule_time' is required."
                    )
                if frequency == AutomationRule.ScheduleFrequency.WEEKLY and not data.get('schedule_day_of_week'):
                    raise serializers.ValidationError(
                        "For 'WEEKLY' frequency, 'schedule_day_of_week' is required."
                    )
                if frequency == AutomationRule.ScheduleFrequency.MONTHLY and not data.get('schedule_day_of_month'):
                    raise serializers.ValidationError(
                        "For 'MONTHLY' frequency, 'schedule_day_of_month' is required."
                    )
            
        return data


class TriggerEmailSerializer(serializers.Serializer):
    """
    Serializer for validating the trigger email request.
    Organization is determined from the authenticated user.
    """
    automation_name = serializers.CharField(max_length=255, required=False)
    rule_id = serializers.UUIDField(required=False)
    email_template_id = serializers.UUIDField(required=False, allow_null=True)
    reason_name = serializers.ChoiceField(choices=AutomationRule.ReasonName.choices)
    email_variables = serializers.JSONField()
    recipient_emails = serializers.ListField(
        child=serializers.EmailField()
    )

    def validate(self, attrs):
        # Allow direct rule targeting OR reason-based lookup
        if not attrs.get('rule_id') and not attrs.get('automation_name') and not attrs.get('reason_name'):
            raise serializers.ValidationError("Provide rule_id, automation_name, or reason_name.")
        return attrs


class SMSConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for SMS configuration settings (Twilio integration).
    """
    organization_id = serializers.UUIDField(source='organization.id', read_only=True)

    class Meta:
        model = SMSConfigurationModel
        fields = [
            'id', 'name_or_type', 'organization_id', 'endpoint_url', 'account_ssid',
            'auth_token', 'verified_service_id', 'default_from_number',
            'whatsapp_from_number', 'whatsapp_enabled', 'is_active', 'is_published',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'auth_token': {'write_only': True, 'style': {'input_type': 'password'}}
        }

    def create(self, validated_data):
        token = validated_data.get('auth_token')
        if token:
            validated_data['auth_token'] = encrypt_data(token)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        token = validated_data.get('auth_token')
        if token:
            validated_data['auth_token'] = encrypt_data(token)
        return super().update(instance, validated_data)


class SMSTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for SMS templates with dynamic variables.
    """
    organization_id = serializers.UUIDField(source='organization.id', read_only=True)

    class Meta:
        model = SMSTemplate
        fields = [
            'id', 'template_name', 'organization_id', 'sms_body', 'recipient_numbers_list',
            'is_active', 'is_published', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'organization_id', 'created_at', 'updated_at')


class TriggerSMSSerializer(serializers.Serializer):
    """
    Serializer for validating the trigger SMS request.
    """
    reason_name = serializers.CharField(max_length=255, required=False)
    rule_id = serializers.UUIDField(required=False)
    sms_variables = serializers.JSONField(required=False)
    recipient_numbers = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )

    def validate(self, attrs):
        """
        Validate that either reason_name or rule_id is provided.
        """
        if not attrs.get('reason_name') and not attrs.get('rule_id'):
            raise serializers.ValidationError("Either 'reason_name' or 'rule_id' must be provided.")
        return attrs


# Enhanced serializers for organization configuration
class OrganizationEmailConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for organization email configuration"""
    
    organization_id = serializers.UUIDField(source='organization.id', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    usage_percentage_daily = serializers.SerializerMethodField(read_only=True)
    usage_percentage_monthly = serializers.SerializerMethodField(read_only=True)
    can_send_email_status = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = OrganizationEmailConfiguration
        fields = [
            'id', 'organization_id', 'organization_name', 'plan_type', 'plan_limits',
            'default_from_domain', 'custom_domain', 'custom_domain_verified', 'timezone',
            'emails_sent_today', 'emails_sent_this_month', 'last_email_sent_at',
            'is_suspended', 'suspension_reason', 'bounce_rate', 'complaint_rate',
            'reputation_score', 'usage_percentage_daily', 'usage_percentage_monthly',
            'can_send_email_status', 'is_active', 'is_published',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'organization_id', 'organization_name',
            'emails_sent_today', 'emails_sent_this_month', 'last_email_sent_at',
            'bounce_rate', 'complaint_rate', 'reputation_score',
            'created_at', 'updated_at'
        ]
    
    def get_usage_percentage_daily(self, obj):
        daily_limit = obj.get_daily_limit()
        if daily_limit == 0:
            return 0
        return round((obj.emails_sent_today / daily_limit) * 100, 2)
    
    def get_usage_percentage_monthly(self, obj):
        monthly_limit = obj.get_monthly_limit()
        if monthly_limit == 0:
            return 0
        return round((obj.emails_sent_this_month / monthly_limit) * 100, 2)
    
    def get_can_send_email_status(self, obj):
        can_send, reason = obj.can_send_email()
        return {'can_send': can_send, 'reason': reason}


class EmailProviderSerializer(serializers.ModelSerializer):
    """Serializer for email providers"""
    
    organization_id = serializers.UUIDField(source='organization.id', read_only=True, allow_null=True)
    config = serializers.JSONField(write_only=True, required=False)
    config_status = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = EmailProvider
        fields = [
            'id', 'name', 'organization_id', 'provider_type', 'is_shared',
            'max_emails_per_minute', 'max_emails_per_hour', 'max_emails_per_day',
            'is_active', 'is_published', 'is_default', 'priority',
            'health_status', 'config', 'config_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['organization_id', 'encrypted_config', 'health_status', 'last_health_check']
    
    def get_config_status(self, obj):
        try:
            from ..utils.email_providers import EmailProviderFactory
            config = obj.decrypt_config()
            provider = EmailProviderFactory.create_provider(obj.provider_type, config)
            is_valid, message = provider.validate_config(config)
            return {'is_valid': is_valid, 'message': message}
        except Exception as e:
            return {'is_valid': False, 'message': str(e)}
    
    def create(self, validated_data):
        config = validated_data.pop('config', {})
        instance = super().create(validated_data)
        if config:
            instance.encrypt_config(config)
            instance.save()
        return instance
    
    def update(self, instance, validated_data):
        config = validated_data.pop('config', None)
        instance = super().update(instance, validated_data)
        if config is not None:
            instance.encrypt_config(config)
            instance.save()
        return instance


class EnhancedEmailDeliveryLogSerializer(serializers.ModelSerializer):
    """Enhanced serializer for email delivery logs"""
    
    automation_rule_name = serializers.CharField(source='campaigns.automation_name', read_only=True)
    provider_name = serializers.CharField(source='email_provider.name', read_only=True)
    organization_id = serializers.UUIDField(source='organization.id', read_only=True, allow_null=True)
    campaign_id = serializers.UUIDField(source='campaign.id', read_only=True, allow_null=True)
    email_template_id = serializers.UUIDField(source='email_template.id', allow_null=True, read_only=True)
    queue_item_id = serializers.UUIDField(source='queue_item.id', allow_null=True, read_only=True)
    
    class Meta:
        model = EmailDeliveryLog
        fields = [
            'id', 'automation_rule', 'automation_rule_name', 'organization_id', 'campaign_id',
            'reason_name', 'trigger_type', 'recipient_email', 'sender_email',
            'subject', 'delivery_status', 'planned_delivery_at', 'queue_item_id',
            'email_template_id', 'sent_at', 'delivered_at', 'opened_at', 'clicked_at',
            'bounced_at', 'open_count', 'click_count', 'unique_click_count', 'bounce_type',
            'bounce_reason', 'error_message', 'spam_score', 'is_spam', 'is_duplicate',
            'email_provider', 'provider_name', 'provider_message_id', 'user_agent',
            'ip_address', 'event_history', 'context_data', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'sent_at', 'delivered_at', 'opened_at', 'clicked_at', 'bounced_at',
            'open_count', 'click_count', 'unique_click_count', 'spam_score',
            'user_agent', 'ip_address', 'event_history', 'context_data'
        ]


class EnhancedTriggerEmailSerializer(serializers.Serializer):
    """Enhanced serializer for triggering emails with provider support"""
    
    # Rule identification (one required)
    automation_name = serializers.CharField(max_length=255, required=False)
    rule_id = serializers.UUIDField(required=False)
    reason_name = serializers.ChoiceField(choices=AutomationRule.ReasonName.choices, required=False)
    
    # Content
    email_variables = serializers.JSONField(required=True)
    recipient_emails = serializers.ListField(child=serializers.EmailField(), required=True)
    
    # Overrides
    email_template_id = serializers.UUIDField(required=False, allow_null=True)
    preferred_provider_id = serializers.UUIDField(required=False, allow_null=True)
    priority = serializers.IntegerField(min_value=1, max_value=10, required=False)
    
    # Options
    schedule_at = serializers.DateTimeField(required=False, allow_null=True)
    skip_validation = serializers.BooleanField(default=False)
    
    def validate(self, attrs):
        # Ensure at least one rule identification method
        identifiers = [attrs.get('rule_id'), attrs.get('automation_name'), attrs.get('reason_name')]
        if not any(identifiers):
            raise serializers.ValidationError("Provide rule_id, automation_name, or reason_name")
        return attrs